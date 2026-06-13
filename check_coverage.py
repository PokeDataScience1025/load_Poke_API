"""
ポケモンの説明文の網羅性を検証するスクリプト
目的: PokeAPIの説明文データがどの程度充実しているかを確認するためのツール
対象: 図鑑番号1〜50（テスト用。全体を調べる場合は1〜1025に変更してください）
出力内容: 各ポケモンの英語版、日本語（漢字・ja）、日本語（かな・ja-Hrkt）の説明文の有無を一覧表示し、最終的な網羅率をレポートします。
"""

import sys
import time
import requests

# 検証するポケモンの範囲
# ※ 動作テスト用に最初は 1〜50 程度を推奨します。
# ※ 全体（第9世代まで）を調べる場合は 1〜1025 に変更してください。
START_ID = 1
END_ID = 50


def check_pokemon_coverage():
    total_checked = 0
    has_en_count = 0
    has_ja_kanji_count = 0  # ja
    has_ja_kana_count = 0  # ja-Hrkt
    has_any_count = 0  # ja または ja-Hrkt がある
    completely_empty_count = 0  # 説明文自体が空

    print(
        f"【検証開始】図鑑番号 {START_ID} から {END_ID} の説明文（日・英）をチェックします...\n"
    )
    print(
        f"{'ID':<5} | {'名前(英)':<15} | {'EN':<4} | {'JA(漢字)':<8} | {'JA(かな)':<8} | {'日本語有':<6}"
    )
    print("-" * 65)

    for pokemon_id in range(START_ID, END_ID + 1):
        url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/"

        try:
            response = requests.get(url, timeout=10)

            # API負荷軽減のための待機（備忘録のガイドラインを遵守）
            time.sleep(0.3)

            if response.status_code == 404:
                # 途中で欠番がある場合（フォルム違いなどによるID飛び対策）
                continue
            elif response.status_code != 200:
                print(
                    f"ID {pokemon_id}: エラーが発生しました（Status: {response.status_code}）"
                )
                continue

            data = response.json()
            pokemon_name = data["name"]
            total_checked += 1

            entries = data.get("flavor_text_entries", [])

            if not entries:
                completely_empty_count += 1
                print(
                    f"{pokemon_id:<5} | {pokemon_name:<15} | [データ自体が存在しません]"
                )
                continue

            # 言語の存在フラグ
            f_en = False
            f_ja = False
            f_kana = False

            for entry in entries:
                lang = entry["language"]["name"]
                if lang == "en":
                    f_en = True
                elif lang == "ja":
                    f_ja = True
                elif lang == "ja-Hrkt":
                    f_kana = True

            # カウント処理と「日本語有」フラグの作成
            if f_en:
                has_en_count += 1
            if f_ja:
                has_ja_kanji_count += 1
            if f_kana:
                has_ja_kana_count += 1

            has_any_ja_flag = False
            if f_ja or f_kana:
                has_any_count += 1
                has_any_ja_flag = True

            # 1行ずつのステータス表示
            print(
                f"{pokemon_id:<5} | {pokemon_name:<15} | "
                f"{'◯' if f_en else '×':<4} | "
                f"{'◯' if f_ja else '×':<8} | "
                f"{'◯' if f_kana else '×':<8} | "
                f"{'◯' if has_any_ja_flag else '×':<6}"
            )

        except Exception as e:
            print(f"ID {pokemon_id}: エラー発生 ({e})")
            time.sleep(2)

    # 最終レポート出力
    if total_checked == 0:
        print("\n検証されたデータはありませんでした。")
        return

    print("\n" + "=" * 60)
    print("【網羅性 検証結果レポート】")
    print(f"総検証数 (有効な種族数): {total_checked} 匹")
    print("-" * 60)
    print(
        f"・英語版 (en) 網羅率         : {has_en_count / total_checked * 100:.1f}% ({has_en_count}匹)"
    )
    print(
        f"・日本語(漢字/ja) 網羅率      : {has_ja_kanji_count / total_checked * 100:.1f}% ({has_ja_kanji_count}匹)"
    )
    print(
        f"・日本語(かな/ja-Hrkt) 網羅率 : {has_ja_kana_count / total_checked * 100:.1f}% ({has_ja_kana_count}匹)"
    )
    print(
        f"・日本語（いずれかあり）網羅率 : {has_any_count / total_checked * 100:.1f}% ({has_any_count}匹)"
    )
    print(f"・日本語完全欠落（英語のみ等） : {total_checked - has_any_count} 匹")
    print(f"・説明文データ完全不在         : {completely_empty_count} 匹")
    print("=" * 60)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    check_pokemon_coverage()