# Flutter 課金実装スキル（RevenueCat）

FlutterアプリにRevenueCatを使ったサブスクリプション課金を実装するためのスキル。

## 設計方針

- **押し売りしない**: 課金しなくても罪悪感がない
- **シンプル**: 1画面完結、10秒で読める
- **控えめな演出**: 紙吹雪・チェックマーク禁止

## セットアップ

### 1. 依存関係の追加

```yaml
# pubspec.yaml
dependencies:
  purchases_flutter: ^8.0.0
```

### 2. RevenueCatダッシュボード設定

1. https://app.revenuecat.com でアプリを作成
2. APIキーを取得（iOS/Android別）
3. Entitlement（例: `plus`）を作成
4. Product（例: `app_plus_monthly`）を作成

### 3. App Store Connect / Google Play Console

- サブスクリプション商品を作成
- RevenueCatと連携

## 実装テンプレート

### subscription_provider.dart

```dart
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

/// RevenueCat API Keys
const _revenueCatApiKeyIOS = 'appl_XXXXXXXX';
const _revenueCatApiKeyAndroid = 'goog_XXXXXXXX';

/// Product IDs
const monthlyProductId = 'app_plus_monthly';

/// Entitlement ID
const plusEntitlementId = 'plus';

/// CustomerInfo プロバイダー
final customerInfoProvider = StateNotifierProvider<CustomerInfoNotifier, AsyncValue<CustomerInfo?>>((ref) {
  return CustomerInfoNotifier();
});

class CustomerInfoNotifier extends StateNotifier<AsyncValue<CustomerInfo?>> {
  CustomerInfoNotifier() : super(const AsyncValue.loading()) {
    _init();
  }

  void _init() async {
    try {
      final info = await Purchases.getCustomerInfo();
      state = AsyncValue.data(info);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> refresh() async {
    try {
      final info = await Purchases.getCustomerInfo();
      state = AsyncValue.data(info);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

/// Plus会員かどうか
final isPlusProvider = Provider<bool>((ref) {
  final customerInfo = ref.watch(customerInfoProvider);
  return customerInfo.whenOrNull(
    data: (info) => info?.entitlements.active.containsKey(plusEntitlementId) ?? false,
  ) ?? false;
});

/// デバッグ用: Plus状態を強制的に切り替え
final debugPlusOverrideProvider = StateProvider<bool?>((ref) => null);

/// 実効的なPlus状態（デバッグオーバーライド対応）
final effectiveIsPlusProvider = Provider<bool>((ref) {
  final debugOverride = ref.watch(debugPlusOverrideProvider);
  if (debugOverride != null) return debugOverride;
  return ref.watch(isPlusProvider);
});

/// 利用可能なパッケージ
final availablePackagesProvider = FutureProvider<List<Package>>((ref) async {
  try {
    final offerings = await Purchases.getOfferings();
    return offerings.current?.availablePackages ?? [];
  } catch (e) {
    return [];
  }
});

/// RevenueCatを初期化
Future<void> initializeRevenueCat({String? userId}) async {
  final apiKey = Platform.isIOS ? _revenueCatApiKeyIOS : _revenueCatApiKeyAndroid;
  await Purchases.setLogLevel(kDebugMode ? LogLevel.debug : LogLevel.error);
  final configuration = PurchasesConfiguration(apiKey);
  if (userId != null) configuration.appUserID = userId;
  await Purchases.configure(configuration);
}

/// 購入を実行
Future<bool> purchasePackage(Package package) async {
  try {
    final result = await Purchases.purchasePackage(package);
    return result.entitlements.active.containsKey(plusEntitlementId);
  } catch (e) {
    if (e is PurchasesErrorCode && e == PurchasesErrorCode.purchaseCancelledError) {
      return false;
    }
    rethrow;
  }
}

/// 購入を復元
Future<bool> restorePurchases() async {
  final info = await Purchases.restorePurchases();
  return info.entitlements.active.containsKey(plusEntitlementId);
}
```

### paywall_screen.dart（課金画面）

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

class PaywallScreen extends ConsumerStatefulWidget {
  const PaywallScreen({super.key});

  @override
  ConsumerState<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends ConsumerState<PaywallScreen> {
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    final packagesAsync = ref.watch(availablePackagesProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('App Plus')),
      body: packagesAsync.when(
        data: (packages) => _buildContent(context, packages),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => const Center(child: Text('読み込みエラー')),
      ),
    );
  }

  Widget _buildContent(BuildContext context, List<Package> packages) {
    final theme = Theme.of(context);
    final monthlyPackage = packages.firstWhere(
      (p) => p.packageType == PackageType.monthly,
      orElse: () => packages.first,
    );

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // タイトル
            Text(
              'いつものアプリを、\nもっと気持ちよく。',
              style: theme.textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),

            // 特典リスト
            _buildFeature('🧘', '広告が一切表示されません'),
            _buildFeature('📸', '機能を無制限で使えます'),
            _buildFeature('☁️', 'いつもの使い心地のまま'),
            const SizedBox(height: 32),

            // 価格
            Text(
              '月額 ${monthlyPackage.storeProduct.priceString}',
              style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            Text('いつでも解約できます', style: theme.textTheme.bodySmall),
            const SizedBox(height: 24),

            // 購入ボタン
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _isLoading ? null : () => _handlePurchase(monthlyPackage),
                child: _isLoading
                    ? const CircularProgressIndicator()
                    : const Text('Plusにする'),
              ),
            ),
            const SizedBox(height: 12),

            // キャンセル
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('今は無料で使う'),
            ),
            const SizedBox(height: 16),

            // フッター
            Text(
              '無料でも、これまで通り使えます。\nPlusは「応援したい人」向けのプランです。',
              style: theme.textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeature(String emoji, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 24)),
          const SizedBox(width: 12),
          Text(text),
        ],
      ),
    );
  }

  Future<void> _handlePurchase(Package package) async {
    setState(() => _isLoading = true);
    try {
      final success = await purchasePackage(package);
      if (success && mounted) {
        ref.read(customerInfoProvider.notifier).refresh();
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const PlusSuccessScreen()),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }
}
```

### plus_success_screen.dart（課金完了画面）

```dart
import 'package:flutter/material.dart';

/// 課金完了画面（控えめな演出）
class PlusSuccessScreen extends StatelessWidget {
  const PlusSuccessScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(),

              // アイコン（小さめ）
              Icon(Icons.water_drop_outlined, size: 48,
                color: theme.colorScheme.primary.withOpacity(0.6)),
              const SizedBox(height: 32),

              // メッセージ
              Text('ありがとう。', style: theme.textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text('これで、もっと気持ちよく使えます。',
                style: theme.textTheme.bodyLarge),
              const SizedBox(height: 24),
              Text('広告は表示されなくなりました。\nいつも通り、続けてください。',
                style: theme.textTheme.bodyMedium,
                textAlign: TextAlign.center),

              const Spacer(),

              // ボタン
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst),
                  child: const Text('使い続ける'),
                ),
              ),
              const SizedBox(height: 48),
            ],
          ),
        ),
      ),
    );
  }
}
```

## 課金導線の配置ルール

### OK: 設定画面（常設）
```dart
ListTile(
  title: const Text('App Plus'),
  subtitle: const Text('広告なしで使う'),
  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PaywallScreen())),
)
```

### OK: 動画広告ダイアログ内（小さく）
```dart
Text('Plusなら、広告なしで使えます', style: theme.textTheme.bodySmall)
```

### NG: 使わない文言
- ❌ 制限 / 解放
- ❌ 今だけ / おすすめ / お得
- ❌ アップグレードしないと...

## 使用例

### main.dart で初期化

```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeRevenueCat();
  runApp(const ProviderScope(child: MyApp()));
}
```

### 課金状態の確認

```dart
final isPlus = ref.watch(effectiveIsPlusProvider);
if (isPlus) {
  // Plus会員向けの処理
}
```

### デバッグ用切り替え（開発者画面など）

```dart
// Plus状態を強制オン
ref.read(debugPlusOverrideProvider.notifier).state = true;

// 自動（実際の状態）に戻す
ref.read(debugPlusOverrideProvider.notifier).state = null;
```
