import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
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

  Future<void> _pickAndUploadFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt', 'doc', 'docx'],
        withData: true, // Need bytes for web compatibility
      );

      if (result != null && result.files.single.bytes != null) {
        final fileBytes = result.files.single.bytes!;
        final fileName = result.files.single.name;
        final text = _messageController.text.trim();
        _messageController.clear();

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Uploading file...')),
        );

        final newMessage = await _chatService.uploadFileAndSendMessage(
          widget.chatId,
          text,
          fileBytes,
          fileName,
        );

        setState(() {
          _messages.insert(0, newMessage);
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('File upload failed: $e')),
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
                          final hasFile = msg['file_url'] != null && msg['file_url'].toString().isNotEmpty;

                          return ListTile(
                            title: Text(msg['content'] ?? ''),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('User ${msg['sender_id']}'),
                                if (hasFile)
                                  Padding(
                                    padding: const EdgeInsets.only(top: 4.0),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.attachment, size: 16),
                                        const SizedBox(width: 4),
                                        Expanded(
                                          child: Text(
                                            'Attachment: ${msg['file_url'].split('/').last}',
                                            style: const TextStyle(
                                              fontStyle: FontStyle.italic,
                                              color: Colors.blue,
                                            ),
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                              ],
                            ),
                          );
                        },
                      ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.attach_file),
                  onPressed: _pickAndUploadFile,
                  color: Colors.grey,
                ),
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
