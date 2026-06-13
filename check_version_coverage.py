"""
ポケモンの説明文のバージョン別データ数を検証するスクリプト
目的: PokeAPIの説明文データがどの程度バージョン別に充実しているかを確認するためのツール
対象: 図鑑番号1〜30（テスト用。全体を調べる場合は1〜1025に変更してください）
出力内容: 各ポケモンの英語版、日本語（漢字・ja）、日本語（かな・ja-Hrkt）の説明文が登録されている作品数を一覧表示し、最終的な平均登録作品数をレポートします。
"""

import sys
import time
import requests

# 検証するポケモンの範囲（最初は1〜30程度でテストし、問題なければ1〜1025に拡大してください）
START_ID = 1
END_ID = 30


def check_version_density():
    total_checked = 0

    # 各言語の「1匹あたりの平均バージョン登録数」を測るための合計カウンター
    total_en_versions = 0
    total_ja_kanji_versions = 0  # ja
    total_ja_kana_versions = 0  # ja-Hrkt

    print(
        f"【検証開始】図鑑番号 {START_ID} から {END_ID} の「バージョン別データ数」を調査します...\n"
    )
    print(
        f"{'ID':<5} | {'名前(英)':<15} | {'EN作品数':<8} | {'JA漢字作品数':<10} | {'JAかな作品数':<10}"
    )
    print("-" * 65)

    for pokemon_id in range(START_ID, END_ID + 1):
        url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/"

        try:
            response = requests.get(url, timeout=10)
            time.sleep(0.3)  # Fair Use Policyに基づくウェイト

            if response.status_code == 404:
                continue
            elif response.status_code != 200:
                print(f"ID {pokemon_id}: エラー ({response.status_code})")
                continue

            data = response.json()
            pokemon_name = data["name"]
            total_checked += 1

            entries = data.get("flavor_text_entries", [])

            # このポケモンにおける、各言語のユニークなバージョン（作品）のセット
            en_versions = set()
            ja_kanji_versions = set()
            ja_kana_versions = set()

            for entry in entries:
                lang = entry["language"]["name"]
                version_name = entry["version"]["name"]

                if lang == "en":
                    en_versions.add(version_name)
                elif lang == "ja":
                    ja_kanji_versions.add(version_name)
                elif lang == "ja-Hrkt":
                    ja_kana_versions.add(version_name)

            # カウンターに加算
            total_en_versions += len(en_versions)
            total_ja_kanji_versions += len(ja_kanji_versions)
            total_ja_kana_versions += len(ja_kana_versions)

            # 1匹ずつの詳細を表示
            print(
                f"{pokemon_id:<5} | {pokemon_name:<15} | "
                f"{len(en_versions):<8} | "
                f"{len(ja_kanji_versions):<10} | "
                f"{len(ja_kana_versions):<10}"
            )

        except Exception as e:
            print(f"ID {pokemon_id}: エラー発生 ({e})")
            time.sleep(2)

    if total_checked == 0:
        print("\n検証されたデータはありませんでした。")
        return

    # 最終レポート
    print("\n" + "=" * 60)
    print("【バージョン別データ 密度検証レポート】")
    print(f"総検証数: {total_checked} 匹")
    print("-" * 60)
    print(
        f"・1匹あたりの平均【英語 (en)】登録作品数         : {total_en_versions / total_checked:.1f} 作品"
    )
    print(
        f"・1匹あたりの平均【日本語漢字 (ja)】登録作品数   : {total_ja_kanji_versions / total_checked:.1f} 作品"
    )
    print(
        f"・1匹あたりの平均【日本語かな (ja-Hrkt)】登録作品数: {total_ja_kana_versions / total_checked:.1f} 作品"
    )
    print("=" * 60)
    print(
        "※注: 初代ポケモン（フシギダネ等）は、英語だと歴代20作品以上の説明文が"
    )
    print(
        "     びっしり格納されていますが、日本語だと数作品分しかありません。"
    )
    print("=" * 60)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    check_version_density();