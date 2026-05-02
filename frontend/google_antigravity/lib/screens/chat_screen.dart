import 'package:flutter/material.dart';
import '../services/chat_service.dart';
import '../services/websocket_service.dart';

class ChatScreen extends StatefulWidget {
  final int chatId;
  final String chatName;

  const ChatScreen({super.key, required this.chatId, required this.chatName});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _chatService = ChatService();
  final _wsService = WebSocketService();
  final _messageController = TextEditingController();
  List<dynamic> _messages = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadMessages();
    _wsService.connect(widget.chatId, _handleNewMessage);
  }

  @override
  void dispose() {
    _wsService.disconnect();
    _messageController.dispose();
    super.dispose();
  }

  void _handleNewMessage(Map<String, dynamic> message) {
    if (mounted) {
      setState(() {
        // Prevent duplicate if we already added optimistically
        // Simple check: compare content/sender to latest (assuming id might not be in ws payload immediately)
        bool exists = false;
        if (_messages.isNotEmpty && _messages[0]['content'] == message['content'] && _messages[0]['sender_id'] == message['sender_id']) {
            exists = true;
        }

        if (!exists) {
            _messages.insert(0, message);
        }
      });
    }
  }

  Future<void> _loadMessages() async {
    try {
      final messages = await _chatService.getMessages(widget.chatId);
      setState(() {
        _messages = messages.reversed.toList(); // Reverse if backend returns newest first
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load messages: $e')),
        );
      }
    }
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    _messageController.clear();

    try {
      final newMessage = await _chatService.sendMessage(widget.chatId, text);
      setState(() {
        // Optimistically add to UI, we'll implement websockets later
        _messages.insert(0, newMessage);
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to send message: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.chatName),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() {
                _isLoading = true;
              });
              _loadMessages();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _messages.isEmpty
                    ? const Center(child: Text('No messages yet.'))
                    : ListView.builder(
                        reverse: true,
                        itemCount: _messages.length,
                        itemBuilder: (context, index) {
                          final msg = _messages[index];
                          // Basic UI for message
                          return ListTile(
                            title: Text(msg['content'] ?? ''),
                            subtitle: Text('User ${msg['sender_id']}'),
                          );
                        },
                      ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: const InputDecoration(
                      hintText: 'Type a message...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _sendMessage,
                  color: Theme.of(context).primaryColor,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
