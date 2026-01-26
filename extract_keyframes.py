#!/usr/bin/env python3
"""
Video Keyframe Extraction Skill for Claude Code

動画から差分が大きいキーフレームのみを抽出し、
画質とサイズを下げてトークンコストを削減します。

通常: 5秒の動画 → 約450円
最適化後: 5秒の動画 → 約24円（約1/19に削減）
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError:
    print("必要なパッケージをインストールしてください:")
    print("  pip install opencv-python numpy Pillow")
    sys.exit(1)


def calculate_similarity(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """
    2つのフレーム間の類似度を計算（ヒストグラム比較）

    Args:
        frame1: 1つ目のフレーム
        frame2: 2つ目のフレーム

    Returns:
        類似度 (0.0 - 1.0)
    """
    # グレースケールに変換
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # ヒストグラムを計算
    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])

    # 正規化
    cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

    # 相関係数で類似度を計算
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    return max(0.0, similarity)


def extract_keyframes(
    video_path: str,
    output_dir: str,
    similarity_threshold: float = 0.85,
    jpeg_quality: int = 30,
    scale: float = 0.3,
    max_frames: int = 100,
) -> dict:
    """
    動画からキーフレームを抽出

    Args:
        video_path: 入力動画のパス
        output_dir: 出力ディレクトリ
        similarity_threshold: 類似度閾値（これより低いと新しいキーフレームとして抽出）
        jpeg_quality: JPEG品質 (1-100)
        scale: リサイズ倍率 (0.0-1.0)
        max_frames: 最大抽出フレーム数

    Returns:
        抽出結果の情報
    """
    # 動画を開く
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"動画を開けません: {video_path}")

    # 動画情報を取得
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    # 出力ディレクトリを作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # キーフレームを抽出
    keyframes = []
    prev_frame = None
    frame_idx = 0
    extracted_count = 0
    total_size = 0

    print(f"動画情報:")
    print(f"  解像度: {width}x{height}")
    print(f"  フレーム数: {total_frames}")
    print(f"  FPS: {fps:.2f}")
    print(f"  長さ: {duration:.2f}秒")
    print(f"\n抽出設定:")
    print(f"  類似度閾値: {similarity_threshold}")
    print(f"  JPEG品質: {jpeg_quality}")
    print(f"  スケール: {scale}")
    print(f"\nキーフレームを抽出中...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 最初のフレームまたは類似度が閾値より低い場合は抽出
        should_extract = False
        if prev_frame is None:
            should_extract = True
        else:
            similarity = calculate_similarity(prev_frame, frame)
            if similarity < similarity_threshold:
                should_extract = True

        if should_extract and extracted_count < max_frames:
            # リサイズ
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # BGRからRGBに変換してPIL Imageに
            rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)

            # JPEG保存
            output_file = output_path / f"frame_{frame_idx:04d}.jpg"
            pil_image.save(output_file, "JPEG", quality=jpeg_quality, optimize=True)

            file_size = output_file.stat().st_size
            total_size += file_size
            keyframes.append({
                "frame_idx": frame_idx,
                "file": str(output_file),
                "size": file_size,
            })
            extracted_count += 1
            prev_frame = frame.copy()

        frame_idx += 1

    cap.release()

    # 新しいサイズを計算
    new_width = int(width * scale)
    new_height = int(height * scale)

    # トークン数を推定（Claude Vision: 約1トークン/750ピクセル）
    pixels_per_frame = new_width * new_height
    tokens_per_frame = pixels_per_frame / 750
    total_tokens = int(tokens_per_frame * extracted_count)

    # コストを推定（Claude Opus: $15/1M input tokens）
    cost_usd = (total_tokens / 1_000_000) * 15
    cost_jpy = cost_usd * 150  # 仮のレート

    result = {
        "input_video": video_path,
        "output_dir": str(output_path),
        "original_resolution": f"{width}x{height}",
        "output_resolution": f"{new_width}x{new_height}",
        "total_frames": total_frames,
        "extracted_frames": extracted_count,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "estimated_tokens": total_tokens,
        "estimated_cost_usd": round(cost_usd, 4),
        "estimated_cost_jpy": round(cost_jpy, 2),
        "keyframes": keyframes,
    }

    return result


def print_result(result: dict):
    """結果を表示"""
    print("\n" + "=" * 50)
    print("抽出完了!")
    print("=" * 50)
    print(f"\n項目              変更前         変更後")
    print(f"{'─' * 50}")
    print(f"フレーム数        {result['total_frames']}枚          {result['extracted_frames']}枚")
    print(f"サイズ            {result['original_resolution']}      {result['output_resolution']}")
    print(f"容量              -              {result['total_size_mb']}MB")
    print(f"\nトークン計算:")
    print(f"  {result['output_resolution']} = {result['estimated_tokens']:,}トークン")
    print(f"\nClaude Opus料金:")
    print(f"  ${result['estimated_cost_usd']:.4f} (約{result['estimated_cost_jpy']:.0f}円)")
    print(f"\n出力ディレクトリ: {result['output_dir']}")
    print(f"抽出ファイル数: {result['extracted_frames']}枚")


def main():
    parser = argparse.ArgumentParser(
        description="動画からキーフレームを抽出してClaudeへの入力コストを削減",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python extract_keyframes.py video.mp4
  python extract_keyframes.py video.mp4 -o keyframes -t 0.85 -q 30 -s 0.3

設定の目安:
  - 類似度閾値 (-t): 0.85-0.95 (低いほど多くのフレームを抽出)
  - JPEG品質 (-q): 20-50 (低いほど圧縮率が高い)
  - スケール (-s): 0.2-0.5 (低いほど小さいサイズ)
        """
    )
    parser.add_argument("video", help="入力動画ファイル")
    parser.add_argument("-o", "--output", default="keyframes", help="出力ディレクトリ (default: keyframes)")
    parser.add_argument("-t", "--threshold", type=float, default=0.85, help="類似度閾値 (default: 0.85)")
    parser.add_argument("-q", "--quality", type=int, default=30, help="JPEG品質 (default: 30)")
    parser.add_argument("-s", "--scale", type=float, default=0.3, help="リサイズ倍率 (default: 0.3)")
    parser.add_argument("-m", "--max-frames", type=int, default=100, help="最大抽出フレーム数 (default: 100)")

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"エラー: 動画ファイルが見つかりません: {args.video}")
        sys.exit(1)

    try:
        result = extract_keyframes(
            video_path=args.video,
            output_dir=args.output,
            similarity_threshold=args.threshold,
            jpeg_quality=args.quality,
            scale=args.scale,
            max_frames=args.max_frames,
        )
        print_result(result)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
