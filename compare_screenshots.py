#!/usr/bin/env python3
"""
Screenshot Diff Comparison Skill for Claude Code

2枚のスクリーンショットを比較し、差分をハイライト表示します。
回帰テストやUI変更の確認に便利です。
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("必要なパッケージをインストールしてください:")
    print("  pip install opencv-python numpy Pillow")
    sys.exit(1)


def load_and_resize(image_path: str, target_size: tuple = None) -> np.ndarray:
    """画像を読み込み、必要に応じてリサイズ"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"画像を読み込めません: {image_path}")

    if target_size:
        img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

    return img


def calculate_diff(img1: np.ndarray, img2: np.ndarray) -> tuple:
    """
    2つの画像の差分を計算

    Returns:
        (diff_image, diff_mask, similarity_score, diff_regions)
    """
    # サイズを合わせる
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # グレースケールに変換
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # 差分を計算
    diff = cv2.absdiff(gray1, gray2)

    # 閾値処理でマスクを作成
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    # ノイズ除去
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # 輪郭を検出して差分領域を取得
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    diff_regions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # 小さすぎる領域は無視
            x, y, w, h = cv2.boundingRect(contour)
            diff_regions.append({
                "x": x, "y": y, "width": w, "height": h, "area": area
            })

    # 類似度スコアを計算 (SSIM風)
    total_pixels = gray1.shape[0] * gray1.shape[1]
    diff_pixels = np.count_nonzero(thresh)
    similarity = 1.0 - (diff_pixels / total_pixels)

    return diff, thresh, similarity, diff_regions


def create_diff_visualization(
    img1: np.ndarray,
    img2: np.ndarray,
    diff_mask: np.ndarray,
    diff_regions: list,
    highlight_color: tuple = (255, 0, 255),  # マゼンタ
) -> dict:
    """差分を可視化した画像を生成"""

    # サイズを合わせる
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    h, w = img1.shape[:2]

    # 1. サイドバイサイド比較
    side_by_side = np.hstack([img1, img2])

    # 2. 差分ハイライト画像（img2に差分を重ねる）
    highlight = img2.copy()

    # 差分領域を半透明でハイライト
    overlay = highlight.copy()
    for region in diff_regions:
        x, y, rw, rh = region["x"], region["y"], region["width"], region["height"]
        cv2.rectangle(overlay, (x, y), (x + rw, y + rh), highlight_color, -1)

    cv2.addWeighted(overlay, 0.3, highlight, 0.7, 0, highlight)

    # 差分領域の枠を描画
    for region in diff_regions:
        x, y, rw, rh = region["x"], region["y"], region["width"], region["height"]
        cv2.rectangle(highlight, (x, y), (x + rw, y + rh), highlight_color, 2)

    # 3. 差分のみの画像
    diff_only = np.zeros_like(img1)
    diff_mask_3ch = cv2.cvtColor(diff_mask, cv2.COLOR_GRAY2BGR)
    diff_only = cv2.bitwise_and(img2, diff_mask_3ch)

    # 4. ブレンド比較（変更前後を重ねる）
    blend = cv2.addWeighted(img1, 0.5, img2, 0.5, 0)

    return {
        "side_by_side": side_by_side,
        "highlight": highlight,
        "diff_only": diff_only,
        "blend": blend,
    }


def compare_screenshots(
    image1_path: str,
    image2_path: str,
    output_dir: str,
    scale: float = 1.0,
    jpeg_quality: int = 85,
) -> dict:
    """
    2枚のスクリーンショットを比較

    Args:
        image1_path: 変更前の画像（ベースライン）
        image2_path: 変更後の画像
        output_dir: 出力ディレクトリ
        scale: 出力画像のスケール
        jpeg_quality: JPEG品質

    Returns:
        比較結果の情報
    """
    # 画像を読み込む
    img1 = load_and_resize(image1_path)
    img2 = load_and_resize(image2_path)

    print(f"比較中...")
    print(f"  変更前: {image1_path} ({img1.shape[1]}x{img1.shape[0]})")
    print(f"  変更後: {image2_path} ({img2.shape[1]}x{img2.shape[0]})")

    # 差分を計算
    diff, diff_mask, similarity, diff_regions = calculate_diff(img1, img2)

    # 可視化画像を生成
    visualizations = create_diff_visualization(img1, img2, diff_mask, diff_regions)

    # 出力ディレクトリを作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 画像を保存
    saved_files = {}
    for name, img in visualizations.items():
        # リサイズ
        if scale != 1.0:
            new_size = (int(img.shape[1] * scale), int(img.shape[0] * scale))
            img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

        output_file = output_path / f"diff_{name}.jpg"
        cv2.imwrite(str(output_file), img, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        saved_files[name] = str(output_file)

    # 結果をまとめる
    result = {
        "image1": image1_path,
        "image2": image2_path,
        "similarity_score": round(similarity * 100, 2),
        "is_identical": len(diff_regions) == 0,
        "diff_region_count": len(diff_regions),
        "diff_regions": diff_regions,
        "output_files": saved_files,
    }

    return result


def print_result(result: dict):
    """結果を表示"""
    print("\n" + "=" * 50)
    print("比較完了!")
    print("=" * 50)

    similarity = result["similarity_score"]
    if result["is_identical"]:
        status = "✓ 同一"
    elif similarity >= 95:
        status = "△ ほぼ同じ（軽微な差分あり）"
    elif similarity >= 80:
        status = "△ 一部変更あり"
    else:
        status = "✗ 大きく異なる"

    print(f"\n類似度: {similarity}% {status}")
    print(f"差分領域数: {result['diff_region_count']}箇所")

    if result["diff_regions"]:
        print(f"\n差分領域の詳細:")
        for i, region in enumerate(result["diff_regions"][:5], 1):
            print(f"  {i}. 位置({region['x']}, {region['y']}) "
                  f"サイズ({region['width']}x{region['height']})")
        if len(result["diff_regions"]) > 5:
            print(f"  ... 他 {len(result['diff_regions']) - 5} 箇所")

    print(f"\n出力ファイル:")
    for name, path in result["output_files"].items():
        print(f"  - {name}: {path}")

    print(f"\nClaudeに渡す推奨ファイル:")
    print(f"  {result['output_files']['highlight']}")


def main():
    parser = argparse.ArgumentParser(
        description="2枚のスクリーンショットを比較して差分をハイライト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python compare_screenshots.py before.png after.png
  python compare_screenshots.py before.png after.png -o diff_output -s 0.5

出力ファイル:
  - diff_side_by_side.jpg: 左右に並べた比較
  - diff_highlight.jpg: 差分箇所をハイライト表示
  - diff_only.jpg: 差分のみ表示
  - diff_blend.jpg: 2枚を半透明で重ねた画像
        """
    )
    parser.add_argument("image1", help="変更前の画像（ベースライン）")
    parser.add_argument("image2", help="変更後の画像")
    parser.add_argument("-o", "--output", default="diff_output", help="出力ディレクトリ (default: diff_output)")
    parser.add_argument("-s", "--scale", type=float, default=1.0, help="出力画像のスケール (default: 1.0)")
    parser.add_argument("-q", "--quality", type=int, default=85, help="JPEG品質 (default: 85)")

    args = parser.parse_args()

    for path in [args.image1, args.image2]:
        if not os.path.exists(path):
            print(f"エラー: 画像ファイルが見つかりません: {path}")
            sys.exit(1)

    try:
        result = compare_screenshots(
            image1_path=args.image1,
            image2_path=args.image2,
            output_dir=args.output,
            scale=args.scale,
            jpeg_quality=args.quality,
        )
        print_result(result)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
