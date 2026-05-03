import 'package:flutter/material.dart';
import '../services/task_service.dart';
import '../services/task_list_service.dart';

class KanbanScreen extends StatefulWidget {
  final int? chatId;
  final int? taskListId;
  final String? globalFilter; // e.g. "all", "today", "upcoming", "inbox"
  final String boardName;

  const KanbanScreen({
    super.key,
    this.chatId,
    this.taskListId,
    this.globalFilter,
    required this.boardName,
  }) : assert(chatId != null || taskListId != null || globalFilter != null, 'Provide chatId, taskListId or globalFilter');

  @override
  State<KanbanScreen> createState() => _KanbanScreenState();
}

class _KanbanScreenState extends State<KanbanScreen> {
  final _taskService = TaskService();
  final _taskListService = TaskListService();

  List<dynamic> _tasks = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadTasks();
  }

  Future<void> _loadTasks() async {
    setState(() => _isLoading = true);
    try {
      List<dynamic> tasks;
      if (widget.globalFilter != null) {
        tasks = await _taskService.getGlobalTasks(widget.globalFilter!);
      } else if (widget.chatId != null) {
        tasks = await _taskService.getChatTasks(widget.chatId!);
      } else {
        tasks = await _taskListService.getTasksInList(widget.taskListId!);
      }
      setState(() {
        _tasks = tasks;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load tasks: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _updateTaskStatus(Map<String, dynamic> task, String newStatus) async {
    // Optimistic update
    setState(() {
      task['status'] = newStatus;
    });

    try {
      if (widget.globalFilter != null) {
         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(content: Text('Cannot drag&drop in Smart Lists yet. Updating from here requires a unified task endpoint.')),
        );
        await _loadTasks();
        return;
      } else if (widget.chatId != null) {
        await _taskService.updateTaskStatus(widget.chatId!, task['id'], newStatus);
      } else {
        await _taskListService.updateTaskStatus(widget.taskListId!, task['id'], newStatus);
      }
    } catch (e) {
      // Revert on failure
      await _loadTasks();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to update status: $e')),
        );
      }
    }
  }

  void _showCreateTaskDialog() {
    final titleController = TextEditingController();
    String priority = 'medium';

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: const Text('New Task'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: titleController,
                    decoration: const InputDecoration(labelText: 'Task Title'),
                  ),
                  DropdownButton<String>(
                    value: priority,
                    items: ['low', 'medium', 'high', 'urgent'].map((String value) {
                      return DropdownMenuItem<String>(
                        value: value,
                        child: Text(value),
                      );
                    }).toList(),
                    onChanged: (val) {
                      setState(() {
                        priority = val!;
                      });
                    },
                  )
                ],
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                ElevatedButton(
                  onPressed: () async {
                    final title = titleController.text.trim();
                    if (title.isNotEmpty) {
                      Navigator.pop(context);
                      try {
                        if (widget.globalFilter != null) {
                           // For MVP, if creating from a global view, we could create an inbox task.
                           // I'll skip it for now to keep UI simple, or we can use the inbox endpoint if it's the "inbox" filter.
                           ScaffoldMessenger.of(context).showSnackBar(
                             const SnackBar(content: Text('Create tasks inside specific chats or lists.')),
                           );
                        } else if (widget.chatId != null) {
                          await _taskService.createChatTask(widget.chatId!, title, priority);
                        } else {
                          await _taskListService.createTaskInList(widget.taskListId!, title, priority);
                        }
                        _loadTasks();
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Failed to create task: $e')),
                          );
                        }
                      }
                    }
                  },
                  child: const Text('Create'),
                ),
              ],
            );
          }
        );
      },
    );
  }

  Widget _buildColumn(String title, String status) {
    final columnTasks = _tasks.where((t) => t['status'] == status).toList();

    return Expanded(
      child: DragTarget<Map<String, dynamic>>(
        onWillAcceptWithDetails: (details) => details.data['status'] != status,
        onAcceptWithDetails: (details) {
          _updateTaskStatus(details.data, status);
        },
        builder: (context, candidateData, rejectedData) {
          return Container(
            margin: const EdgeInsets.all(4.0),
            decoration: BoxDecoration(
              color: candidateData.isNotEmpty ? Colors.blue.withOpacity(0.2) : Colors.grey[200],
              borderRadius: BorderRadius.circular(8.0),
            ),
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: columnTasks.length,
                    itemBuilder: (context, index) {
                      final task = columnTasks[index];
                      return Draggable<Map<String, dynamic>>(
                        data: task,
                        feedback: Material(
                          elevation: 4.0,
                          child: Container(
                            padding: const EdgeInsets.all(16),
                            color: Colors.white,
                            width: 200,
                            child: Text(task['title']),
                          ),
                        ),
                        childWhenDragging: Opacity(
                          opacity: 0.5,
                          child: Card(
                            child: ListTile(title: Text(task['title'])),
                          ),
                        ),
                        child: Card(
                          child: ListTile(
                            title: Text(task['title']),
                            subtitle: Text('Priority: ${task['priority']}'),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Board: ${widget.boardName}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadTasks,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Row(
              children: [
                _buildColumn('To Do', 'todo'),
                _buildColumn('In Progress', 'in_progress'),
                _buildColumn('Done', 'done'),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateTaskDialog,
        child: const Icon(Icons.add),
      ),
    );
  }
}
