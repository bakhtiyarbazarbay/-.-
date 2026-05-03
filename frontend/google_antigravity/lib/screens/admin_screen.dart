import 'package:flutter/material.dart';
import '../services/admin_service.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _adminService = AdminService();

  List<dynamic> _users = [];
  List<dynamic> _chats = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final users = await _adminService.getAllUsers();
      final chats = await _adminService.getAllChats();
      setState(() {
        _users = users;
        _chats = chats;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading admin data: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  // --- Users Tab Methods ---

  Future<void> _toggleUserStatus(int userId, bool currentStatus) async {
    try {
      await _adminService.updateUserAdmin(userId, null, !currentStatus);
      _loadData();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to update status: $e')),
        );
      }
    }
  }

  Future<void> _changeUserRole(int userId, String newRole) async {
    try {
      await _adminService.updateUserAdmin(userId, newRole, null);
      _loadData();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to update role: $e')),
        );
      }
    }
  }

  void _showRoleDialog(Map<String, dynamic> user) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Change Role for ${user['full_name'] ?? user['email']}'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: ['student', 'starosta', 'assistant', 'admin'].map((role) {
              return ListTile(
                title: Text(role),
                trailing: user['role'] == role ? const Icon(Icons.check) : null,
                onTap: () {
                  Navigator.pop(context);
                  if (user['role'] != role) {
                    _changeUserRole(user['id'], role);
                  }
                },
              );
            }).toList(),
          ),
        );
      },
    );
  }

  // --- Chats Tab Methods ---

  Future<void> _deleteChat(int chatId) async {
    bool confirm = await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Chat'),
        content: const Text('Are you sure you want to delete this chat completely? This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete', style: TextStyle(color: Colors.red))),
        ],
      ),
    ) ?? false;

    if (!confirm) return;

    try {
      await _adminService.deleteChat(chatId);
      _loadData();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to delete chat: $e')),
        );
      }
    }
  }

  void _showTransferOwnershipDialog(int chatId, String chatName) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Transfer Ownership: $chatName'),
          content: TextField(
            controller: controller,
            decoration: const InputDecoration(labelText: 'New Creator User ID'),
            keyboardType: TextInputType.number,
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                final newIdStr = controller.text.trim();
                if (newIdStr.isEmpty) return;
                final newId = int.tryParse(newIdStr);
                if (newId != null) {
                  Navigator.pop(context);
                  try {
                    await _adminService.transferChatOwnership(chatId, newId);
                    _loadData();
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Transfer failed: $e')),
                      );
                    }
                  }
                }
              },
              child: const Text('Transfer'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.people), text: 'Users'),
            Tab(icon: Icon(Icons.forum), text: 'Chats'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                // Tab 1: Users
                ListView.builder(
                  itemCount: _users.length,
                  itemBuilder: (context, index) {
                    final user = _users[index];
                    return ListTile(
                      title: Text(user['email']),
                      subtitle: Text('Role: ${user['role']} | ID: ${user['id']}'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit),
                            onPressed: () => _showRoleDialog(user),
                            tooltip: 'Change Role',
                          ),
                          Switch(
                            value: user['is_active'],
                            onChanged: (val) => _toggleUserStatus(user['id'], user['is_active']),
                          ),
                        ],
                      ),
                    );
                  },
                ),
                // Tab 2: Chats
                ListView.builder(
                  itemCount: _chats.length,
                  itemBuilder: (context, index) {
                    final chat = _chats[index];
                    return ListTile(
                      title: Text(chat['name'] ?? 'Unnamed Chat'),
                      subtitle: Text('Creator ID: ${chat['created_by']} | Type: ${chat['chat_type']}'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.transform),
                            onPressed: () => _showTransferOwnershipDialog(chat['id'], chat['name'] ?? 'Unnamed'),
                            tooltip: 'Transfer Ownership',
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => _deleteChat(chat['id']),
                            tooltip: 'Delete Chat',
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ],
            ),
    );
  }
}
