import 'dart:convert';
import 'dart:io' show Platform;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  WebSocketChannel? _channel;

  String get baseWsUrl {
    final configuredUrl = dotenv.env['WS_URL'];
    if (configuredUrl != null && configuredUrl.isNotEmpty) {
      return configuredUrl;
    }

    try {
      if (Platform.isAndroid) {
        return 'ws://10.0.2.2:8000/ws';
      }
    } catch (e) {}
    return 'ws://127.0.0.1:8000/ws';
  }

  void connect(int chatId, Function(Map<String, dynamic>) onMessageReceived) {
    _channel = WebSocketChannel.connect(
      Uri.parse('$baseWsUrl/$chatId'),
    );

    _channel!.stream.listen((message) {
      final decodedMessage = jsonDecode(message);
      onMessageReceived(decodedMessage);
    }, onError: (error) {
      print('WebSocket error: $error');
    }, onDone: () {
      print('WebSocket disconnected');
    });
  }

  void disconnect() {
    _channel?.sink.close();
  }
}
