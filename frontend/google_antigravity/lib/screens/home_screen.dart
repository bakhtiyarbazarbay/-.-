import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/chat_service.dart';
import '../services/task_list_service.dart';
import 'login_screen.dart';
import 'chat_screen.dart';
import 'admin_screen.dart';
import 'kanban_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _authService = AuthService();
  final _chatService = ChatService();
  final _taskListService = TaskListService();

  List<dynamic> _chats = [];
  List<dynamic> _taskLists = [];
  Map<String, dynamic>? _currentUser;

  bool _isLoadingChats = true;
  bool _isLoadingTaskLists = true;
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    try {
      final user = await _authService.getCurrentUser();
      if (mounted) {
        setState(() {
          _currentUser = user;
        });
      }
      await _loadChats();
      await _loadTaskLists();
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingChats = false;
          _isLoadingTaskLists = false;
        });
      }
    }
  }

  Future<void> _loadChats() async {
    try {
      final chats = await _chatService.getMyChats();
      if (mounted) {
        setState(() {
          _chats = chats;
          _isLoadingChats = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingChats = false;
        });
      }
    }
  }

  Future<void> _loadTaskLists() async {
    try {
      final taskLists = await _taskListService.getMyTaskLists();
      if (mounted) {
        setState(() {
          _taskLists = taskLists;
          _isLoadingTaskLists = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingTaskLists = false;
        });
      }
    }
  }

  Future<void> _logout() async {
    await _authService.logout();
    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const LoginScreen()),
      );
    }
  }

  void _showCreateChatDialog() {
    final nameController = TextEditingController();
    final descController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Create New Chat'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Chat Name'),
              ),
              TextField(
                controller: descController,
                decoration: const InputDecoration(labelText: 'Description'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final name = nameController.text.trim();
                final desc = descController.text.trim();
                if (name.isNotEmpty) {
                  Navigator.pop(context); // Close dialog immediately
                  setState(() => _isLoadingChats = true);
                  try {
                    await _chatService.createChat(name, desc);
                    await _loadChats(); // Reload list
                  } catch (e) {
                    setState(() => _isLoadingChats = false);
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Failed to create chat: $e')),
                      );
                    }
                  }
                }
              },
              child: const Text('Create'),
            ),
          ],
        );
      },
    );
  }

  void _showCreateTaskListDialog() {
    final nameController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Create Personal List'),
          content: TextField(
            controller: nameController,
            decoration: const InputDecoration(labelText: 'List Name'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final name = nameController.text.trim();
                if (name.isNotEmpty) {
                  Navigator.pop(context);
                  setState(() => _isLoadingTaskLists = true);
                  try {
                    await _taskListService.createTaskList(name);
                    await _loadTaskLists();
                  } catch (e) {
                    setState(() => _isLoadingTaskLists = false);
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Failed to create list: $e')),
                      );
                    }
                  }
                }
              },
              child: const Text('Create'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    Widget bodyContent;
    FloatingActionButton? fab;
    String appBarTitle;

    if (_currentIndex == 0) {
      // Chats Tab
      appBarTitle = 'Google Antigravity - Chats';
      fab = FloatingActionButton(
        onPressed: _showCreateChatDialog,
        child: const Icon(Icons.add),
      );
      bodyContent = _isLoadingChats
          ? const Center(child: CircularProgressIndicator())
          : _chats.isEmpty
              ? const Center(child: Text('No chats found.'))
              : ListView.builder(
                  itemCount: _chats.length,
                  itemBuilder: (context, index) {
                    final chat = _chats[index];
                    return ListTile(
                      leading: const CircleAvatar(
                        child: Icon(Icons.chat),
                      ),
                      title: Text(chat['name'] ?? 'Unnamed Chat'),
                      subtitle: Text(chat['description'] ?? 'No description'),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ChatScreen(
                              chatId: chat['id'],
                              chatName: chat['name'] ?? 'Unnamed Chat',
                            ),
                          ),
                        );
                      },
                    );
                  },
                );
    } else {
      // Personal Lists Tab
      appBarTitle = 'My Personal Lists';
      fab = FloatingActionButton(
        onPressed: _showCreateTaskListDialog,
        child: const Icon(Icons.add),
      );
      bodyContent = _isLoadingTaskLists
          ? const Center(child: CircularProgressIndicator())
          : _taskLists.isEmpty
              ? const Center(child: Text('No personal lists found.'))
              : ListView.builder(
                  itemCount: _taskLists.length,
                  itemBuilder: (context, index) {
                    final taskList = _taskLists[index];
                    return ListTile(
                      leading: const CircleAvatar(
                        backgroundColor: Colors.orange,
                        child: Icon(Icons.list, color: Colors.white),
                      ),
                      title: Text(taskList['name']),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => KanbanScreen(
                              taskListId: taskList['id'],
                              boardName: taskList['name'],
                            ),
                          ),
                        );
                      },
                    );
                  },
                );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(appBarTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              if (_currentIndex == 0) {
                setState(() => _isLoadingChats = true);
                _loadChats();
              } else {
                setState(() => _isLoadingTaskLists = true);
                _loadTaskLists();
              }
            },
          ),
        ],
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            UserAccountsDrawerHeader(
              accountName: Text(_currentUser?['full_name'] ?? 'Loading...'),
              accountEmail: Text(_currentUser?['email'] ?? ''),
              currentAccountPicture: const CircleAvatar(
                backgroundColor: Colors.white,
                child: Icon(Icons.person),
              ),
            ),
            if (_currentUser?['role'] == 'admin')
              ListTile(
                leading: const Icon(Icons.admin_panel_settings),
                title: const Text('Admin Dashboard'),
                onTap: () {
                  Navigator.pop(context); // close drawer
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const AdminScreen()),
                  );
                },
              ),
            ListTile(
              leading: const Icon(Icons.logout),
              title: const Text('Logout'),
              onTap: _logout,
            ),
          ],
        ),
      ),
      body: bodyContent,
      floatingActionButton: fab,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.chat),
            label: 'Chats',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.fact_check),
            label: 'My Lists',
          ),
        ],
      ),
    );
  }
}
