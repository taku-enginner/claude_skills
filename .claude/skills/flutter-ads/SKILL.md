# Flutter 広告実装スキル（AdMob）

FlutterアプリにGoogle AdMob広告を実装するためのスキル。

## 対応広告タイプ

- バナー広告（常設）
- リワード広告（動画広告）
- ネイティブ広告

## セットアップ

### 1. 依存関係の追加

```yaml
# pubspec.yaml
dependencies:
  google_mobile_ads: ^5.2.0
```

### 2. iOS設定

```xml
<!-- ios/Runner/Info.plist -->
<key>GADApplicationIdentifier</key>
<string>ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX</string>
<key>SKAdNetworkItems</key>
<array>
  <dict>
    <key>SKAdNetworkIdentifier</key>
    <string>cstr6suwn9.skadnetwork</string>
  </dict>
</array>
```

### 3. Android設定

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<meta-data
    android:name="com.google.android.gms.ads.APPLICATION_ID"
    android:value="ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX"/>
```

## 実装テンプレート

### ad_provider.dart

```dart
import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

/// バナー広告の高さ定数
const double kBannerAdHeight = 50.0;

/// AdMob初期化状態プロバイダー
final adInitializedProvider = StateProvider<bool>((ref) => false);

/// 広告を表示すべきかどうか（課金ユーザーは非表示）
final shouldShowAdsProvider = Provider<bool>((ref) {
  // TODO: 課金状態を確認
  return true;
});

/// バナー広告ユニットID
String get bannerAdUnitId {
  if (kDebugMode) {
    return Platform.isIOS
        ? 'ca-app-pub-3940256099942544/2934735716'  // テスト用
        : 'ca-app-pub-3940256099942544/6300978111';
  } else {
    return Platform.isIOS
        ? 'ca-app-pub-XXXXX/XXXXX'  // 本番用
        : 'ca-app-pub-XXXXX/XXXXX';
  }
}

/// リワード広告ユニットID
String get rewardedAdUnitId {
  if (kDebugMode) {
    return Platform.isIOS
        ? 'ca-app-pub-3940256099942544/1712485313'
        : 'ca-app-pub-3940256099942544/5224354917';
  } else {
    return Platform.isIOS
        ? 'ca-app-pub-XXXXX/XXXXX'
        : 'ca-app-pub-XXXXX/XXXXX';
  }
}

/// AdMobを初期化
Future<void> initializeAdMob() async {
  await MobileAds.instance.initialize();
}

/// リワード広告マネージャー
class RewardedAdManager {
  RewardedAd? _rewardedAd;
  bool _isLoading = false;

  /// リワード広告をプリロード
  Future<void> loadAd() async {
    if (_isLoading || _rewardedAd != null) return;

    _isLoading = true;
    await RewardedAd.load(
      adUnitId: rewardedAdUnitId,
      request: const AdRequest(),
      rewardedAdLoadCallback: RewardedAdLoadCallback(
        onAdLoaded: (ad) {
          _rewardedAd = ad;
          _isLoading = false;
        },
        onAdFailedToLoad: (error) {
          _isLoading = false;
          debugPrint('RewardedAd failed to load: ${error.message}');
        },
      ),
    );
  }

  bool get isReady => _rewardedAd != null;

  /// リワード広告を表示
  Future<bool> showAd() async {
    if (_rewardedAd == null) return false;

    final completer = Completer<bool>();

    _rewardedAd!.fullScreenContentCallback = FullScreenContentCallback(
      onAdDismissedFullScreenContent: (ad) {
        ad.dispose();
        _rewardedAd = null;
        loadAd();
      },
      onAdFailedToShowFullScreenContent: (ad, error) {
        ad.dispose();
        _rewardedAd = null;
        if (!completer.isCompleted) completer.complete(false);
        loadAd();
      },
    );

    await _rewardedAd!.show(
      onUserEarnedReward: (ad, reward) {
        if (!completer.isCompleted) completer.complete(true);
      },
    );

    return completer.future;
  }

  void dispose() {
    _rewardedAd?.dispose();
    _rewardedAd = null;
  }
}

/// グローバルなリワード広告マネージャー
final rewardedAdManagerProvider = Provider<RewardedAdManager>((ref) {
  final manager = RewardedAdManager();
  ref.onDispose(() => manager.dispose());
  return manager;
});
```

### banner_ad_widget.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

class BannerAdWidget extends ConsumerStatefulWidget {
  const BannerAdWidget({super.key});

  @override
  ConsumerState<BannerAdWidget> createState() => _BannerAdWidgetState();
}

class _BannerAdWidgetState extends ConsumerState<BannerAdWidget> {
  BannerAd? _bannerAd;
  bool _isLoaded = false;

  @override
  void initState() {
    super.initState();
    _loadAd();
  }

  void _loadAd() {
    _bannerAd = BannerAd(
      adUnitId: bannerAdUnitId,
      size: AdSize.banner,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: (ad) {
          if (mounted) setState(() => _isLoaded = true);
        },
        onAdFailedToLoad: (ad, error) {
          ad.dispose();
        },
      ),
    )..load();
  }

  @override
  void dispose() {
    _bannerAd?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isLoaded || _bannerAd == null) {
      return const SizedBox(height: 50);
    }
    return SizedBox(
      height: 50,
      child: AdWidget(ad: _bannerAd!),
    );
  }
}
```

### rewarded_ad_dialog.dart（動画広告ダイアログ）

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum RewardedAdDialogResult { watched, cancelled, failed }

/// リワード広告確認ダイアログを表示
Future<RewardedAdDialogResult> showRewardedAdDialog({
  required BuildContext context,
  required WidgetRef ref,
  String title = 'もう少しだけ続ける？',
  String message = '続けるには短い動画を1回だけ見てね。',
}) async {
  final result = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('今日はここまで'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: const Text('動画を見る'),
        ),
      ],
    ),
  );

  if (result != true) return RewardedAdDialogResult.cancelled;

  final adManager = ref.read(rewardedAdManagerProvider);
  if (!adManager.isReady) {
    await adManager.loadAd();
    await Future.delayed(const Duration(seconds: 3));
  }

  if (!adManager.isReady) return RewardedAdDialogResult.failed;

  final success = await adManager.showAd();
  return success ? RewardedAdDialogResult.watched : RewardedAdDialogResult.failed;
}
```

## 使用例

### main.dart で初期化

```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeAdMob();
  runApp(const ProviderScope(child: MyApp()));
}
```

### リワード広告の表示

```dart
// 使用回数制限時などに表示
final result = await showRewardedAdDialog(context: context, ref: ref);
if (result == RewardedAdDialogResult.watched) {
  // 広告視聴完了 → 機能を継続
}
```

## 課金ユーザーの広告非表示

```dart
// shouldShowAdsProvider を課金状態と連携
final shouldShowAdsProvider = Provider<bool>((ref) {
  final isSubscribed = ref.watch(isSubscribedProvider);
  return !isSubscribed;
});

// Widget内で条件分岐
if (ref.watch(shouldShowAdsProvider)) {
  return const BannerAdWidget();
} else {
  return const SizedBox.shrink();
}
```
