import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:io' show Platform;

class TaskListService {
  String get baseUrl {
    final configuredUrl = dotenv.env['API_URL'];
    if (configuredUrl != null && configuredUrl.isNotEmpty) {
      return '$configuredUrl/task-lists';
    }

    const String apiPath = '/api/v1/task-lists';
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000$apiPath';
      }
    } catch (e) {}
    return 'http://127.0.0.1:8000$apiPath';
  }

  Future<List<dynamic>> getMyTaskLists() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.get(
      Uri.parse('$baseUrl/'),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load task lists');
    }
  }

  Future<Map<String, dynamic>> createTaskList(String name) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.post(
      Uri.parse('$baseUrl/'),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'name': name,
      }),
    );

    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to create task list');
    }
  }

  Future<void> deleteTaskList(int listId) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.delete(
      Uri.parse('$baseUrl/$listId'),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 204) {
      throw Exception('Failed to delete task list');
    }
  }

  Future<List<dynamic>> getTasksInList(int listId) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.get(
      Uri.parse('$baseUrl/$listId/tasks/'),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load tasks for list');
    }
  }

  Future<Map<String, dynamic>> createTaskInList(int listId, String title, String priority) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.post(
      Uri.parse('$baseUrl/$listId/tasks/'),
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
      throw Exception('Failed to create task in list');
    }
  }

  Future<Map<String, dynamic>> updateTaskStatus(int listId, int taskId, String newStatus) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final response = await http.put(
      Uri.parse('$baseUrl/$listId/tasks/$taskId'),
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
      throw Exception('Failed to update task status in list');
    }
  }
}
