
// name: ui-skills-flutter
// description: Opinionated constraints for building better interfaces with agents in Dart/Flutter projects.

# UI Skills (Flutter/Dart)

When invoked, apply these opinionated constraints to Flutter UI work.

## How to use

- `/ui-skills`
  Apply these constraints to any UI work in this conversation.

- `/ui-skills <file or dir>`
  Review the specified file(s) against all constraints and output:
    - violations (quote exact line/snippet)
    - why it matters (1 short sentence)
    - a concrete fix (code-level suggestion)

## Stack

- MUST use Flutter Material 3 defaults (ThemeData(useMaterial3: true)) unless custom tokens already exist or are explicitly requested
- SHOULD use `ColorScheme` and semantic tokens over hardcoded colors
- MUST use `flutter_animate` or `ImplicitlyAnimated` widgets (`AnimatedOpacity`, `AnimatedScale`, etc.) for micro/entrance animations
- MUST use a `build`-time class composition helper for conditional styles (e.g. helper functions instead of stringly classes)
- SHOULD use `riverpod` or `flutter_riverpod` for state where testability and DI are needed; keep `setState` scoped to simple, local UI
- MUST respect `MediaQuery` and `ViewPadding` (safe areas) for fixed elements (`SafeArea`, `SliverSafeArea`)

## Components

- MUST use accessible widgets for anything with keyboard/focus behavior: `Focus`, `FocusTraversalGroup`, `Shortcuts`, `Actions`
- MUST add `semanticsLabel` for icon-only buttons/icons (`Semantics`, `IconButton(tooltip: ...)`)
- MUST prefer existing project component primitives first (design system widgets)
- NEVER mix primitive systems within the same interaction surface (e.g., two different shortcut/focus systems overlapping)
- SHOULD use `NavigationBar`/`BottomAppBar`/`AppBar` with proper semantics and tooltips
- NEVER rebuild keyboard or focus behavior by hand unless explicitly requested—use `Shortcuts` + `Actions` + `Intent` pattern or `RawKeyboardListener` only when necessary

## Interaction

- MUST use a `AlertDialog` or `Dialog` with explicit confirmation for destructive/irreversible actions
- SHOULD use skeletons/placeholders for loading states (`Shimmer` or simple grey boxes) rather than spinners in dense lists
- NEVER use full-screen fixed heights; prefer `MediaQuery.size.height` with `SafeArea` or `LayoutBuilder` constraints
- MUST respect `safe-area` (`SafeArea` or `Padding` from `MediaQuery.viewPadding`) for fixed positioned elements
- MUST show errors next to where the action happens (inline `Text` or `HelperText` near the control), not only via SnackBar
- NEVER block paste in `TextField` or `TextFormField` (do not override `inputFormatters` to block paste)

## Animation

- NEVER add animation unless explicitly requested
- MUST animate only compositor-friendly props: `opacity`, `transform` (`scale`, `translate`, `rotate`)
- NEVER animate layout properties: `width`, `height`, `margin`, `padding`, or expensive relayout triggers
- SHOULD avoid animating paint-heavy props (`BoxShadow` blur, large `BackdropFilter`) except small, local UI (icons, text)
- SHOULD use ease-out on entrance (`Curves.easeOut`, `Curves.easeOutCubic`)
- NEVER exceed `200ms` for interaction feedback; entrances typically `120–200ms`
- MUST pause or dispose looping animations when off-screen (`TickerMode`, `Visibility`, or lifecycle-aware controllers)
- SHOULD respect `MediaQuery.of(context).disableAnimations` / `AccessibilityFeatures.disableAnimations` (or equivalent) and provide `Duration.zero` fallbacks
- NEVER introduce custom cubic bezier curves unless explicitly requested
- SHOULD avoid animating large images or full-screen surfaces

## Typography

- MUST balance headings (`Text` with `textAlign: TextAlign.start` and wrapping) and use `TextWidthBasis.longestLine` where appropriate to avoid ragged text
- MUST use tabular numerals for data when using a font that supports it (e.g., set `FontFeature.tabularFigures()` via `TextStyle.fontFeatures`)
- SHOULD use `TextOverflow.ellipsis` or `maxLines` for dense UI; prefer `LayoutBuilder` + `RichText` for complex clamps
- NEVER modify letter-spacing (`TextStyle.letterSpacing`) unless explicitly requested

## Layout

- MUST use a fixed `z-index`-like layering via `Stack` order or a documented elevation scale; avoid arbitrary `Stack` index juggling
- SHOULD use square sizing via `SizedBox.square` or `ConstrainedBox` instead of separately setting width + height
- SHOULD use `Slivers` for scrollable complex layouts; avoid nesting scroll views that fight each other
- MUST use `Padding`/`SizedBox`/`Spacer` for spacing; avoid magic numbers—document spacing tokens in Theme

## Performance

- NEVER animate large `BackdropFilter` or `ImageFiltered.blur` surfaces
- NEVER apply `RepaintBoundary`/`willChange`-like hints outside an active animation; use `RepaintBoundary` only where profiling shows benefit
- NEVER use `setState`/`useEffect`-equivalents (e.g., `addPostFrameCallback`) for logic that can be expressed declaratively in `build` with state providers/selectors
- SHOULD memoize expensive widgets with `const` constructors and `const` styles
- MUST avoid rebuilding heavy lists; prefer `ListView.builder`/`SliverList` with keyed items

## Design

- NEVER use gradients unless explicitly requested
- NEVER use purple or multicolor gradients
- NEVER use glow effects as primary affordances
- SHOULD use Material default shadow/elevation scale unless explicitly requested
- MUST give empty states one clear next action (primary button or link)
- SHOULD limit accent color usage to one per view
- SHOULD use existing theme or `ColorScheme` tokens before introducing new ones

## Example fixes (snippets)

- Icon-only button missing semantics

  // violations:
  //   IconButton(icon: Icon(Icons.delete))
  // why it matters:
  //   Screen readers need labels for non-text controls.
  // fix:
  IconButton(
    icon: const Icon(Icons.delete),
    tooltip: '削除',
    onPressed: handleDelete,
  )

- Unsafe fixed element without safe-area

  // violations:
  //   Positioned(bottom: 0, child: MyBar())
  // why it matters:
  //   Overlaps home indicator / notch on modern devices.
  // fix:
  SafeArea(
    minimum: EdgeInsets.zero,
    child: Align(
      alignment: Alignment.bottomCenter,
      child: MyBar(),
    ),
  )

- Animating layout property (height)

  // violations:
  //   AnimatedContainer(duration: Duration(milliseconds: 400), height: expanded ? 300 : 100)
  // why it matters:
  //   Layout animation is janky; use transform/opacity.
  // fix:
  AnimatedOpacity(
    duration: const Duration(milliseconds: 180),
    curve: Curves.easeOut,
    opacity: expanded ? 1 : 0,
    child: Transform.scale(
      scale: expanded ? 1.0 : 0.96,
      child: const MyContent(),
    ),
  )

- Error placement far from the action

  // violations:
  //   ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('エラー')))
  // why it matters:
  //   Users may miss context; error should be near the control.
  // fix:
  Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      TextField(
        controller: controller,
        decoration: const InputDecoration(labelText: '金額'),
        onChanged: validate,
      ),
      if (error != null)
        Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Text(error!, style: Theme.of(context).textTheme.bodySmall!.copyWith(color: Theme.of(context).colorScheme.error)),
        ),
    ],
  )

## Notes

- Treat any non-adopted stack items as Not Applicable and map principles to Flutter equivalents.
- Keep interactions consistent with a single primitives system (Material or your design system), and document exceptions explicitly.