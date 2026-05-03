import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:io' show Platform;

class TaskService {
  String _getBaseUrl(int chatId) {
    final configuredUrl = dotenv.env['API_URL'];
    if (configuredUrl != null && configuredUrl.isNotEmpty) {
      return '$configuredUrl/chats/$chatId/tasks';
    }

    const String apiPath = '/api/v1/chats';
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000$apiPath/$chatId/tasks';
      }
    } catch (e) {}
    return 'http://127.0.0.1:8000$apiPath/$chatId/tasks';
  }

  Future<List<dynamic>> getChatTasks(int chatId) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.get(
      Uri.parse('${_getBaseUrl(chatId)}/'),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load tasks');
    }
  }

  Future<Map<String, dynamic>> createChatTask(int chatId, String title, String priority) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.post(
      Uri.parse('${_getBaseUrl(chatId)}/'),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'title': title,
        'priority': priority,
      }),
    );

    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to create task');
    }
  }

  Future<Map<String, dynamic>> updateTaskStatus(int chatId, int taskId, String newStatus) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.put(
      Uri.parse('${_getBaseUrl(chatId)}/$taskId'),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'status': newStatus,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to update task status');
    }
  }
}
