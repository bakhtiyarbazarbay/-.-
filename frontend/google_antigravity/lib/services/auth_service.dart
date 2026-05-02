import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'dart:io' show Platform;

class AuthService {
  String get baseUrl {
    final configuredUrl = dotenv.env['API_URL'];
    if (configuredUrl != null && configuredUrl.isNotEmpty) {
      return '$configuredUrl/auth';
    }

    // Fallback if .env is missing
    const String apiPath = '/api/v1/auth';
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000$apiPath';
      }
    } catch (e) {
      // Web fallback
    }
    return 'http://127.0.0.1:8000$apiPath';
  }

  Future<String?> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/login'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(response.body);
      final String token = data['access_token'];

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('jwt_token', token);

      return token;
    } else {
      throw Exception('Failed to login: ${response.body}');
    }
  }

  Future<void> register(String email, String password, String fullName) async {
    final response = await http.post(
      Uri.parse('$baseUrl/register'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'email': email,
        'password': password,
        'full_name': fullName,
      }),
    );

    if (response.statusCode != 201) {
      throw Exception('Failed to register: ${response.body}');
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('jwt_token');
  }
}
