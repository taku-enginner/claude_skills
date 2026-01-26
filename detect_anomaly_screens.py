#!/usr/bin/env python3
"""
Error/Anomaly Screen Detection Skill for Claude Code

動画やスクリーンショットからエラー画面や異常な画面を自動検出します。
- 赤いエラー表示
- ダイアログ/ポップアップ
- 空白画面
- クラッシュ画面
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError:
    print("必要なパッケージをインストールしてください:")
    print("  pip install opencv-python numpy Pillow")
    sys.exit(1)


class AnomalyDetector:
    """異常画面を検出するクラス"""

    def __init__(self):
        # エラー表示でよく使われる赤色の範囲 (HSV)
        self.error_red_lower = np.array([0, 100, 100])
        self.error_red_upper = np.array([10, 255, 255])
        self.error_red_lower2 = np.array([160, 100, 100])
        self.error_red_upper2 = np.array([180, 255, 255])

        # 警告でよく使われる黄色/オレンジの範囲 (HSV)
        self.warning_lower = np.array([15, 100, 100])
        self.warning_upper = np.array([35, 255, 255])

    def detect_red_error(self, frame: np.ndarray) -> Dict:
        """赤いエラー表示を検出"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 赤色マスク（2つの範囲を結合）
        mask1 = cv2.inRange(hsv, self.error_red_lower, self.error_red_upper)
        mask2 = cv2.inRange(hsv, self.error_red_lower2, self.error_red_upper2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        # 赤色の割合を計算
        red_ratio = np.count_nonzero(red_mask) / red_mask.size

        # 連続した赤い領域を検出
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large_red_regions = [c for c in contours if cv2.contourArea(c) > 500]

        return {
            "detected": red_ratio > 0.01 or len(large_red_regions) > 0,
            "red_ratio": round(red_ratio * 100, 2),
            "red_region_count": len(large_red_regions),
            "type": "error_red"
        }

    def detect_warning(self, frame: np.ndarray) -> Dict:
        """警告表示（黄色/オレンジ）を検出"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        warning_mask = cv2.inRange(hsv, self.warning_lower, self.warning_upper)

        warning_ratio = np.count_nonzero(warning_mask) / warning_mask.size

        contours, _ = cv2.findContours(warning_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large_warning_regions = [c for c in contours if cv2.contourArea(c) > 500]

        return {
            "detected": warning_ratio > 0.02 or len(large_warning_regions) > 0,
            "warning_ratio": round(warning_ratio * 100, 2),
            "warning_region_count": len(large_warning_regions),
            "type": "warning"
        }

    def detect_blank_screen(self, frame: np.ndarray) -> Dict:
        """空白/白画面を検出"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 白に近いピクセルの割合
        white_mask = gray > 240
        white_ratio = np.count_nonzero(white_mask) / white_mask.size

        # 黒に近いピクセルの割合
        black_mask = gray < 15
        black_ratio = np.count_nonzero(black_mask) / black_mask.size

        # 単色に近いかチェック
        std_dev = np.std(gray)

        is_blank = (white_ratio > 0.9 or black_ratio > 0.9) and std_dev < 20

        return {
            "detected": is_blank,
            "white_ratio": round(white_ratio * 100, 2),
            "black_ratio": round(black_ratio * 100, 2),
            "uniformity": round(std_dev, 2),
            "type": "blank_screen"
        }

    def detect_dialog(self, frame: np.ndarray) -> Dict:
        """ダイアログ/ポップアップを検出"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # エッジ検出
        edges = cv2.Canny(gray, 50, 150)

        # 矩形を検出
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2

        dialog_candidates = []
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cw * ch
            aspect_ratio = cw / ch if ch > 0 else 0

            # ダイアログの特徴をチェック
            # - 画面の中央付近にある
            # - 適度なサイズ（画面の10-80%）
            # - 横長または正方形に近い
            is_centered = (abs(x + cw/2 - center_x) < w * 0.3 and
                          abs(y + ch/2 - center_y) < h * 0.3)
            is_dialog_size = 0.05 < area / (w * h) < 0.8
            is_dialog_shape = 0.5 < aspect_ratio < 3.0

            if is_centered and is_dialog_size and is_dialog_shape:
                dialog_candidates.append({
                    "x": x, "y": y, "width": cw, "height": ch
                })

        return {
            "detected": len(dialog_candidates) > 0,
            "dialog_count": len(dialog_candidates),
            "dialogs": dialog_candidates[:3],  # 最大3つまで
            "type": "dialog"
        }

    def detect_loading(self, frame: np.ndarray) -> Dict:
        """ローディング画面を検出（円形のインジケータなど）"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 円を検出
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, 1, 50,
            param1=100, param2=30, minRadius=20, maxRadius=100
        )

        # 画面の中央付近に円があるかチェック
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2

        loading_indicators = []
        if circles is not None:
            for circle in circles[0]:
                cx, cy, r = circle
                # 中央付近にあるか
                if abs(cx - center_x) < w * 0.3 and abs(cy - center_y) < h * 0.3:
                    loading_indicators.append({
                        "x": int(cx), "y": int(cy), "radius": int(r)
                    })

        return {
            "detected": len(loading_indicators) > 0,
            "indicator_count": len(loading_indicators),
            "type": "loading"
        }

    def analyze_frame(self, frame: np.ndarray) -> Dict:
        """フレームを総合的に分析"""
        results = {
            "error_red": self.detect_red_error(frame),
            "warning": self.detect_warning(frame),
            "blank_screen": self.detect_blank_screen(frame),
            "dialog": self.detect_dialog(frame),
            "loading": self.detect_loading(frame),
        }

        # 検出された異常をリストアップ
        anomalies = []
        severity = "normal"

        if results["error_red"]["detected"]:
            anomalies.append("エラー表示（赤）")
            severity = "error"
        if results["blank_screen"]["detected"]:
            anomalies.append("空白画面")
            severity = "error" if severity != "error" else severity
        if results["warning"]["detected"]:
            anomalies.append("警告表示")
            if severity == "normal":
                severity = "warning"
        if results["dialog"]["detected"]:
            anomalies.append("ダイアログ/ポップアップ")
            if severity == "normal":
                severity = "info"
        if results["loading"]["detected"]:
            anomalies.append("ローディング")
            if severity == "normal":
                severity = "info"

        results["summary"] = {
            "has_anomaly": len(anomalies) > 0,
            "anomalies": anomalies,
            "severity": severity,
        }

        return results


def process_video(
    video_path: str,
    output_dir: str,
    sample_interval: int = 10,
    jpeg_quality: int = 50,
    scale: float = 0.5,
) -> Dict:
    """動画から異常画面を検出"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"動画を開けません: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    detector = AnomalyDetector()
    anomaly_frames = []
    frame_idx = 0

    print(f"動画を分析中: {video_path}")
    print(f"  フレーム数: {total_frames}, FPS: {fps:.2f}")
    print(f"  サンプリング間隔: {sample_interval}フレームごと")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_interval == 0:
            results = detector.analyze_frame(frame)

            if results["summary"]["has_anomaly"]:
                timestamp = frame_idx / fps if fps > 0 else 0

                # 画像を保存
                if scale != 1.0:
                    h, w = frame.shape[:2]
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

                filename = f"anomaly_{frame_idx:06d}_{results['summary']['severity']}.jpg"
                filepath = output_path / filename
                cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])

                anomaly_frames.append({
                    "frame_idx": frame_idx,
                    "timestamp": round(timestamp, 2),
                    "timestamp_str": f"{int(timestamp // 60)}:{timestamp % 60:05.2f}",
                    "severity": results["summary"]["severity"],
                    "anomalies": results["summary"]["anomalies"],
                    "file": str(filepath),
                    "details": {k: v for k, v in results.items() if k != "summary"}
                })

        frame_idx += 1

    cap.release()

    return {
        "video_path": video_path,
        "total_frames": total_frames,
        "analyzed_frames": total_frames // sample_interval,
        "anomaly_count": len(anomaly_frames),
        "anomaly_frames": anomaly_frames,
        "output_dir": str(output_path),
    }


def process_images(
    image_paths: List[str],
    output_dir: str,
    jpeg_quality: int = 50,
    scale: float = 0.5,
) -> Dict:
    """複数の画像から異常画面を検出"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    detector = AnomalyDetector()
    anomaly_images = []

    print(f"画像を分析中: {len(image_paths)}枚")

    for i, image_path in enumerate(image_paths):
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"  警告: 読み込めません: {image_path}")
            continue

        results = detector.analyze_frame(frame)

        if results["summary"]["has_anomaly"]:
            # 画像を保存
            if scale != 1.0:
                h, w = frame.shape[:2]
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

            filename = f"anomaly_{i:04d}_{results['summary']['severity']}.jpg"
            filepath = output_path / filename
            cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])

            anomaly_images.append({
                "original_file": image_path,
                "severity": results["summary"]["severity"],
                "anomalies": results["summary"]["anomalies"],
                "output_file": str(filepath),
                "details": {k: v for k, v in results.items() if k != "summary"}
            })

    return {
        "total_images": len(image_paths),
        "anomaly_count": len(anomaly_images),
        "anomaly_images": anomaly_images,
        "output_dir": str(output_path),
    }


def print_video_result(result: Dict):
    """動画分析結果を表示"""
    print("\n" + "=" * 50)
    print("分析完了!")
    print("=" * 50)

    print(f"\n分析対象: {result['video_path']}")
    print(f"分析フレーム数: {result['analyzed_frames']}")
    print(f"異常検出数: {result['anomaly_count']}件")

    if result["anomaly_frames"]:
        # 深刻度別に集計
        by_severity = {}
        for af in result["anomaly_frames"]:
            sev = af["severity"]
            by_severity[sev] = by_severity.get(sev, 0) + 1

        print(f"\n深刻度別:")
        for sev, count in sorted(by_severity.items()):
            icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(sev, "⚪")
            print(f"  {icon} {sev}: {count}件")

        print(f"\n検出された異常画面:")
        for af in result["anomaly_frames"][:10]:
            icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(af["severity"], "⚪")
            anomalies_str = ", ".join(af["anomalies"])
            print(f"  {icon} [{af['timestamp_str']}] {anomalies_str}")
            print(f"     → {af['file']}")

        if len(result["anomaly_frames"]) > 10:
            print(f"  ... 他 {len(result['anomaly_frames']) - 10} 件")

    print(f"\n出力ディレクトリ: {result['output_dir']}")


def print_image_result(result: Dict):
    """画像分析結果を表示"""
    print("\n" + "=" * 50)
    print("分析完了!")
    print("=" * 50)

    print(f"\n分析画像数: {result['total_images']}")
    print(f"異常検出数: {result['anomaly_count']}件")

    if result["anomaly_images"]:
        print(f"\n検出された異常画面:")
        for ai in result["anomaly_images"]:
            icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(ai["severity"], "⚪")
            anomalies_str = ", ".join(ai["anomalies"])
            print(f"  {icon} {ai['original_file']}")
            print(f"     {anomalies_str}")
            print(f"     → {ai['output_file']}")

    print(f"\n出力ディレクトリ: {result['output_dir']}")


def main():
    parser = argparse.ArgumentParser(
        description="動画/画像からエラー画面や異常な画面を自動検出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 動画から異常画面を検出
  python detect_anomaly_screens.py video.mp4

  # 複数の画像から検出
  python detect_anomaly_screens.py screenshot1.png screenshot2.png screenshot3.png

  # オプション付き
  python detect_anomaly_screens.py video.mp4 -o anomalies -i 5 -s 0.3

検出対象:
  - エラー表示（赤い警告など）
  - 警告表示（黄色/オレンジ）
  - 空白/白画面
  - ダイアログ/ポップアップ
  - ローディング画面
        """
    )
    parser.add_argument("inputs", nargs="+", help="動画ファイルまたは画像ファイル")
    parser.add_argument("-o", "--output", default="anomaly_output", help="出力ディレクトリ (default: anomaly_output)")
    parser.add_argument("-i", "--interval", type=int, default=10, help="サンプリング間隔（動画のみ、default: 10）")
    parser.add_argument("-s", "--scale", type=float, default=0.5, help="出力画像のスケール (default: 0.5)")
    parser.add_argument("-q", "--quality", type=int, default=50, help="JPEG品質 (default: 50)")

    args = parser.parse_args()

    # 入力ファイルの存在確認
    for path in args.inputs:
        if not os.path.exists(path):
            print(f"エラー: ファイルが見つかりません: {path}")
            sys.exit(1)

    try:
        # 動画か画像かを判定
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        first_ext = Path(args.inputs[0]).suffix.lower()

        if first_ext in video_extensions:
            # 動画として処理
            result = process_video(
                video_path=args.inputs[0],
                output_dir=args.output,
                sample_interval=args.interval,
                jpeg_quality=args.quality,
                scale=args.scale,
            )
            print_video_result(result)
        else:
            # 画像として処理
            result = process_images(
                image_paths=args.inputs,
                output_dir=args.output,
                jpeg_quality=args.quality,
                scale=args.scale,
            )
            print_image_result(result)

    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
