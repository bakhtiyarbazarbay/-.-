import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:io' show Platform;

class AdminService {
  String _getBaseUrl(String path) {
    final configuredUrl = dotenv.env['API_URL'];
    if (configuredUrl != null && configuredUrl.isNotEmpty) {
      return '$configuredUrl$path';
    }

    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000/api/v1$path';
      }
    } catch (e) {}
    return 'http://127.0.0.1:8000/api/v1$path';
  }

  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('jwt_token');
  }

  // Users

  Future<List<dynamic>> getAllUsers() async {
    final token = await _getToken();
    final url = _getBaseUrl('/users/');

    final response = await http.get(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load users: ${response.body}');
    }
  }

  Future<void> updateUserAdmin(int userId, String? role, bool? isActive) async {
    final token = await _getToken();
    final url = _getBaseUrl('/users/$userId/role');

    final Map<String, dynamic> body = {};
    if (role != null) body['role'] = role;
    if (isActive != null) body['is_active'] = isActive;

    final response = await http.put(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to update user: ${response.body}');
    }
  }

  // Chats

  Future<List<dynamic>> getAllChats() async {
    final token = await _getToken();
    final url = _getBaseUrl('/chats/all');

    final response = await http.get(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load all chats: ${response.body}');
    }
  }

  Future<void> deleteChat(int chatId) async {
    final token = await _getToken();
    final url = _getBaseUrl('/chats/$chatId');

    final response = await http.delete(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 204) {
      throw Exception('Failed to delete chat: ${response.body}');
    }
  }

  Future<void> transferChatOwnership(int chatId, int newCreatorId) async {
    final token = await _getToken();
    final url = _getBaseUrl('/chats/$chatId/creator?new_creator_id=$newCreatorId');

    final response = await http.put(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to transfer ownership: ${response.body}');
    }
  }
}
