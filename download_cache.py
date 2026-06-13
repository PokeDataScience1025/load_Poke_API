"""
ポケモン図鑑番号範囲を指定してRAWデータをキャッシュするスクリプト
- START_ID～END_IDの図鑑番号のポケモンを対象に、/pokemon を主軸にして関連する /pokemon-species と /evolution-chain のデータも紐付けてキャッシュします。
- 取得したデータは、pokemon_cache.json に統合保存されます。
- APIのFair Use Policyに準拠し、リクエスト間隔を500ms以上空けるとともに、429エラーやサーバーエラー時には指数バックオフで再試行します。
- 50匹ごとに定期的にディスクに保存することで、途中でのデータ損失を防止します。
- すでにキャッシュされている進化チェーンは再取得せず、効率的にデータを構築します。
- 10001番以降は必ず存在する /pokemon を主軸にすることで、欠番の影響を最小限に抑え、確実にデータを構築します。
【使用方法】
1. このスクリプトを実行すると、pokemon_cache.json にデータが保存されます。
2. すでに pokemon_cache.json が存在する場合は、そこからデータを読み込み、未取得のIDのみを処理します。
【注意事項】
- APIのFair Use Policyを厳守するため、リクエスト間隔を500ms以上空けることを徹底してください。
- 429エラーやサーバーエラーが発生した場合は、指数バックオフで再試行するため、処理に時間がかかることがあります。焦らずに待機してください。
- 10001番以降は必ず存在する /pokemon を主軸にするため、欠番の影響を最小限に抑え、確実にデータを構築します。
"""

import json
import os
import sys
import time
import requests
from requests.exceptions import RequestException

# 一般ポケモンの範囲
START_ID = 1
END_ID = 1025

# # フォルムチェンジ、メガシンカ、パラドックスポケモン等の範囲
# START_ID = 10001
# END_ID = 10277

CACHE_FILE = "pokemon_cache.json"


def fetch_with_backoff(url):
    """
    Fair Use Policyに準拠したリクエスト関数
    429(Too Many Requests)やサーバーエラー時に、指数バックオフで待機時間を増やしながら再試行します。
    """
    wait_time = 1.0  # 初期待機時間（秒）
    max_retries = 5  # 最大リトライ回数

    for attempt in range(max_retries):
        try:
            res = requests.get(url, timeout=10)
            
            # 正常、または404（データなし）はそのまま返す
            if res.status_code in [200, 404]:
                time.sleep(0.5)  # 推奨ガイドラインに準拠したリクエスト間隔 (500ms)
                return res
            
            # 429エラー、または5xx系サーバーエラーの場合はバックオフ
            if res.status_code == 429 or res.status_code >= 500:
                print(f"\n[警告] サーバー負荷または制限を検知 (Status: {res.status_code})。 {wait_time}秒待機して再試行します...")
                time.sleep(wait_time)
                wait_time *= 2  # 待機時間を倍にする（指数バックオフ）
                continue

        except RequestException as e:
            print(f"\n[通信エラー] {e}。 {wait_time}秒待機して再試行します...")
            time.sleep(wait_time)
            wait_time *= 2
            continue

    return None


def fetch_pokemon_absolute_complete_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            pokemon_cache = json.load(f)
    else:
        pokemon_cache = {}

    downloaded_evo_chains = {}
    for p_data in pokemon_cache.values():
        if "evolution_chain_data" in p_data and p_data["evolution_chain_data"]:
            evo_id = p_data["evolution_chain_data"].get("id")
            if evo_id:
                downloaded_evo_chains[int(evo_id)] = p_data["evolution_chain_data"]

    print(f"図鑑番号 {START_ID} から {END_ID} のRAWデータをキャッシュします...")
    print("-" * 80)

    processed_count = 0

    for p_id in range(START_ID, END_ID + 1):
        str_id = str(p_id)

        if str_id in pokemon_cache:
            continue

        # --- 1. /pokemon の全データ取得 ---
        # 10001番以降は必ず存在する /pokemon を主軸にします
        pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{p_id}/"
        res_pk = fetch_with_backoff(pokemon_url)

        if not res_pk:
            print(f"ID {p_id:<4}: データの取得に失敗し、リトライ上限に達しました。")
            continue
        if res_pk.status_code == 404:
            # データが存在しないID（欠番）は、sleepを挟まずにスキップ
            continue
        
        pk_data = res_pk.json()

        # --- 2. /pokemon-species のデータ取得（存在する場合のみ） ---
        sp_data = None
        evo_chain_data = None
        evo_id = None
        name_ja = pk_data["name"]  # 日本語名が取れなかった場合のフォールバック
        name_en = pk_data["name"]

        # /pokemon のデータ内にある species の URL を利用する
        species_url = pk_data.get("species", {}).get("url", "")
        if species_url:
            res_sp = fetch_with_backoff(species_url)
            if res_sp and res_sp.status_code == 200:
                sp_data = res_sp.json()
                
                # 日本語名の抽出
                for n in sp_data.get("names", []):
                    if n["language"]["name"] == "ja":
                        name_ja = n["name"]
                        break
                name_en = sp_data["name"]

                # --- 3. /evolution-chain のデータ取得 ---
                evo_url = sp_data.get("evolution_chain", {}).get("url", "")
                if evo_url:
                    evo_id = int(evo_url.split("/")[-2])
                    if evo_id in downloaded_evo_chains:
                        evo_chain_data = downloaded_evo_chains[evo_id]
                    else:
                        res_evo = fetch_with_backoff(evo_url)
                        if res_evo and res_evo.status_code == 200:
                            evo_chain_data = res_evo.json()
                            downloaded_evo_chains[evo_id] = evo_chain_data

        # --- RAWデータをパッキング ---
        pokemon_cache[str_id] = {
            "id": p_id,
            "name_en": name_en,
            "name_ja": name_ja,
            "pokemon_data": pk_data,
            "species_data": sp_data,            # 存在しない場合は None
            "evolution_chain_data": evo_chain_data,  # 存在しない場合は None
        }

        print(f"ID {p_id:<4}: 【メモリ保存】 {name_ja:<10} ")
        processed_count += 1

        # 保険として50匹ごとに自動保存
        if processed_count % 50 == 0:
            print(f"\n--- [定期バックアップ] 現在 {processed_count} 匹分の新データをディスクに書き込み中... ---")
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(pokemon_cache, f, ensure_ascii=False, indent=2)
            print("--- [定期バックアップ] 完了。処理を再開します ---\n")

    # 全ループ終了後の最終保存
    print("\n" + "=" * 80)
    print("【最終保存中】すべてのデータをファイルに書き込んでいます...")
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(pokemon_cache, f, ensure_ascii=False, indent=2)
    print(f"【構築完了】すべてのRAWデータを '{CACHE_FILE}' に統合保存しました。")
    print("=" * 80)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    fetch_pokemon_absolute_complete_data()