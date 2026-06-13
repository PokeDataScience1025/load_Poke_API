"""
このスクリプトは、事前にダウンロードして構築したキャッシュファイルから、ユーザーが入力したポケモンの名前（日本語）または図鑑番号をもとに、そのポケモンの図鑑説明文を表示するためのものです。
ユーザーは、コマンドライン上でポケモンの名前やIDを入力することで、そのポケモンの図鑑説明文を確認できます。説明文は、歴代ゲームごとに整理されて表示されます。
【使用方法】
1. まず、download_cache.py を実行してキャッシュファイルを構築してください。
2. 次に、このスクリプトを実行すると、ポケモンの名前（日本語）または図鑑番号を入力するプロンプトが表示されます。
3. 入力後、そのポケモンの図鑑説明文が表示されます。終了するには 'q' を入力してください。
【備考】
- 入力は日本語名または図鑑番号を想定していますが、英語名での検索もサポートしています。その際も、出力は日本語の図鑑説明文になります。
"""

import json
import os
import sys

CACHE_FILE = "pokemon_cache.json"


def load_cache():
    """キャッシュファイルを読み込む"""
    if not os.path.exists(CACHE_FILE):
        print(f"エラー: キャッシュファイル '{CACHE_FILE}' が見つかりません。")
        print("先にダウンロードスクリプトを実行してキャッシュを構築してください。")
        sys.exit(1)

    print("データベースを読み込み中...")
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def find_pokemon(cache, query):
    """入力された文字列（名前またはID）からポケモンデータを検索する"""
    query_str = str(query).strip()

    # 1. まずID（図鑑番号）として検索
    if query_str in cache:
        return cache[query_str]

    # 2. 次に日本語名（name_ja）で検索（大文字小文字・前後の空白を考慮）
    for p_data in cache.values():
        if p_data.get("name_ja") == query_str:
            return p_data

    # 3. 最後に英語名（name_en）でも検索できるようにしておく
    for p_data in cache.values():
        if p_data.get("name_en").lower() == query_str.lower():
            return p_data

    return None


def display_pokedex_texts(pokemon_data):
    """ポケモンの図鑑説明文を整形して表示する"""
    print("\n" + "=" * 60)
    print(
        f" 全国図鑑No.{pokemon_data['id']:<4} | 日本語名: {pokemon_data['name_ja']} | 英語名: {pokemon_data['name_en']}"
    )
    print("=" * 60)

    species_data = pokemon_data.get("species_data")

    # 10001番以降のフォルム違いなど、species_dataを持っていないポケモンの場合
    if not species_data:
        print("※ このIDは特殊フォルム・パラドックスデータです。")
        print(
            "   図鑑説明文は通常フォルム（元の図鑑番号）のデータに統合されています。"
        )
        print("=" * 60)
        return

    # 説明文のエントリを取得
    flavor_text_entries = species_data.get("flavor_text_entries", [])

    if not flavor_text_entries:
        print("図鑑説明文が見つかりませんでした。")
        print("=" * 60)
        return

    print("【歴代ゲームの図鑑説明（日本語）】\n")
    found_any = False
    seen_texts = set()  # 重複表示を避けるためのセット

    for entry in flavor_text_entries:
        # 言語が「日本語(ja)」のものだけを抽出
        if entry.get("language", {}).get("name") == "ja":

            # --- バージョン名を取得 ---
            version_info = entry.get("version", {})
            version_name = version_info.get("name")  # 'red', 'sword' などの文字列を直接取得

            # 万が一 name が取れなかった場合は、URLから切り出しを試みる（予備）
            if not version_name and "url" in version_info:
                url_parts = version_info["url"].strip("/").split("/")
                if url_parts:
                    version_name = url_parts[-1]

            # それでもダメなら 'unknown' にする
            if not version_name:
                version_name = "unknown"

            # 改行コードやフォント固有のゴミ（\n, \fなど）を綺麗に掃除
            flavor_text = (
                entry.get("flavor_text", "")
                .replace("\n", " ")
                .replace("\f", " ")
                .strip()
            )

            # 同じタイトルで全く同じ説明文が複数入っていることがあるため、重複はスキップ
            unique_key = (version_name, flavor_text)
            if unique_key in seen_texts:
                continue
            seen_texts.add(unique_key)

            # 表示を見やすく整形
            print(f"■ [{version_name:<15}]")
            print(f"  {flavor_text}")
            print("-" * 50)
            found_any = True

    if not found_any:
        print("日本語の図鑑説明文が登録されていません。")

    print("=" * 60)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cache = load_cache()
    print(f"総ポケモン数: {len(cache)} 匹のデータをロードしました。")

    while True:
        try:
            print("\n検索したいポケモンの「名前（日本語）」または「図鑑番号」を入力してください。")
            query = input("入力 (終了するには 'q' を入力): ").strip()

            if query.lower() == "q" or query == "":
                print("アプリケーションを終了します。")
                break

            pokemon_data = find_pokemon(cache, query)

            if pokemon_data:
                display_pokedex_texts(pokemon_data)
            else:
                print(f"❌ '{query}' に該当するポケモンは見つかりませんでした。")

        except KeyboardInterrupt:
            print("\nアプリケーションを終了します。")
            break


if __name__ == "__main__":
    main()