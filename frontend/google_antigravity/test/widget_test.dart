import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:google_antigravity/main.dart';

void main() {
  testWidgets('App initializes', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
