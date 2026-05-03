import 'package:flutter/material.dart';
import '../services/chat_service.dart';
import '../services/user_service.dart';
import '../services/auth_service.dart';
import 'home_screen.dart';

class ChatInfoScreen extends StatefulWidget {
  final int chatId;
  final String chatName;

  const ChatInfoScreen({super.key, required this.chatId, required this.chatName});

  @override
  State<ChatInfoScreen> createState() => _ChatInfoScreenState();
}

class _ChatInfoScreenState extends State<ChatInfoScreen> {
  final _chatService = ChatService();
  final _userService = UserService();
  final _authService = AuthService();

  Map<String, dynamic>? _chatDetails;
  List<dynamic> _members = [];
  Map<String, dynamic>? _currentUser;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final chatDetails = await _chatService.getChatDetails(widget.chatId);
      final members = await _chatService.getChatMembers(widget.chatId);
      final currentUser = await _authService.getCurrentUser();

      if (mounted) {
        setState(() {
          _chatDetails = chatDetails;
          _members = members;
          _currentUser = currentUser;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load chat info: $e')),
        );
      }
    }
  }

  bool get _isCreator {
    if (_chatDetails == null || _currentUser == null) return false;
    return _chatDetails!['created_by'] == _currentUser!['id'];
  }

  void _showAddMemberDialog() {
    String searchQuery = '';
    List<dynamic> searchResults = [];
    bool isSearching = false;

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: const Text('Add Member'),
              content: SizedBox(
                width: double.maxFinite,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      decoration: const InputDecoration(
                        labelText: 'Search (Email or Name)',
                        suffixIcon: Icon(Icons.search),
                      ),
                      onChanged: (val) async {
                        searchQuery = val;
                        if (searchQuery.length > 2) {
                          setStateDialog(() => isSearching = true);
                          try {
                            final results = await _userService.searchUsers(searchQuery);
                            setStateDialog(() {
                              searchResults = results;
                              isSearching = false;
                            });
                          } catch (e) {
                            setStateDialog(() => isSearching = false);
                          }
                        } else {
                          setStateDialog(() {
                            searchResults = [];
                          });
                        }
                      },
                    ),
                    const SizedBox(height: 10),
                    if (isSearching) const CircularProgressIndicator(),
                    if (!isSearching)
                      Expanded(
                        child: ListView.builder(
                          shrinkWrap: true,
                          itemCount: searchResults.length,
                          itemBuilder: (context, index) {
                            final user = searchResults[index];
                            final isAlreadyMember = _members.any((m) => m['id'] == user['id']);

                            return ListTile(
                              title: Text(user['full_name'] ?? user['email']),
                              subtitle: Text(user['email']),
                              trailing: isAlreadyMember
                                  ? const Icon(Icons.check, color: Colors.green)
                                  : IconButton(
                                      icon: const Icon(Icons.add),
                                      onPressed: () async {
                                        try {
                                          await _chatService.addChatMembers(widget.chatId, [user['id']]);
                                          Navigator.pop(context);
                                          _loadData();
                                          ScaffoldMessenger.of(context).showSnackBar(
                                            SnackBar(content: Text('${user['full_name']} added to chat')),
                                          );
                                        } catch (e) {
                                          ScaffoldMessenger.of(context).showSnackBar(
                                            SnackBar(content: Text('Failed to add member: $e')),
                                          );
                                        }
                                      },
                                    ),
                            );
                          },
                        ),
                      ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Close'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _removeMember(int userId, String name) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remove Member'),
        content: Text('Are you sure you want to remove $name from the chat?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Remove')),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await _chatService.removeChatMember(widget.chatId, userId);
        _loadData();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('$name removed from chat')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to remove member: $e')),
          );
        }
      }
    }
  }

  Future<void> _leaveChat() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Leave Chat'),
        content: const Text('Are you sure you want to leave this chat?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Leave')),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await _chatService.leaveChat(widget.chatId);
        if (mounted) {
          // Pop ChatInfoScreen
          Navigator.pop(context);
          // Pop ChatScreen and go back to home
          Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(builder: (context) => const HomeScreen()),
            (route) => false,
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to leave chat: $e')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.chatName)),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.chatName} - Info'),
        actions: [
          if (_isCreator)
            IconButton(
              icon: const Icon(Icons.person_add),
              onPressed: _showAddMemberDialog,
              tooltip: 'Add Member',
            ),
        ],
      ),
      body: Column(
        children: [
          if (_chatDetails != null)
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Description: ${_chatDetails!['description'] ?? 'No description'}',
                      style: const TextStyle(fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Type: ${_chatDetails!['chat_type']}', style: const TextStyle(color: Colors.grey)),
                  const Divider(),
                ],
              ),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Members (${_members.length})', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                if (!_isCreator)
                  ElevatedButton(
                    onPressed: _leaveChat,
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red.shade100),
                    child: const Text('Leave Chat', style: TextStyle(color: Colors.red)),
                  ),
              ],
            ),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: _members.length,
              itemBuilder: (context, index) {
                final member = _members[index];
                final isSelf = _currentUser?['id'] == member['id'];
                final isMemberCreator = _chatDetails?['created_by'] == member['id'];

                return ListTile(
                  leading: const CircleAvatar(child: Icon(Icons.person)),
                  title: Text(member['full_name'] ?? member['email'] ?? 'Unknown User'),
                  subtitle: Text(
                      '${member['email']}${isMemberCreator ? ' • Creator' : ''}${isSelf ? ' • You' : ''}'),
                  trailing: (_isCreator && !isSelf && !isMemberCreator)
                      ? IconButton(
                          icon: const Icon(Icons.remove_circle_outline, color: Colors.red),
                          onPressed: () => _removeMember(member['id'], member['full_name'] ?? member['email']),
                        )
                      : null,
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
