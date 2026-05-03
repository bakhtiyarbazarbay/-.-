import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:io' show Platform;

class UserService {
  String get baseUrl {
    final configuredUrl = dotenv.env['API_URL'];
    if (configuredUrl != null && configuredUrl.isNotEmpty) {
      return '$configuredUrl/users';
    }

    const String apiPath = '/api/v1/users';
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000$apiPath';
      }
    } catch (e) {}
    return 'http://127.0.0.1:8000$apiPath';
  }

  Future<List<dynamic>> searchUsers(String query) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('jwt_token');

    final uri = Uri.parse('$baseUrl/search').replace(queryParameters: {
      'query': query,
      'limit': '50',
    });

    final response = await http.get(
      uri,
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to search users: ${response.body}');
    }
  }
}
