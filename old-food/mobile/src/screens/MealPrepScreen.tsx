import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { api } from '../services/api';

interface PrepTask {
  id: number;
  task: string;
  recipe_name: string;
  ingredient?: string;
  technique?: string;
  estimated_time_min: number;
  completed: boolean;
}

interface PrepSchedule {
  tasks: PrepTask[];
  total_time_min: number;
  grouped_by_technique: { [key: string]: PrepTask[] };
  grouped_by_ingredient: { [key: string]: PrepTask[] };
}

export default function MealPrepScreen({ route }: any) {
  const { planId } = route.params;
  const [schedule, setSchedule] = useState<PrepSchedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'technique' | 'ingredient' | 'linear'>('technique');

  useEffect(() => {
    loadPrepSchedule();
  }, [planId]);

  async function loadPrepSchedule() {
    setLoading(true);
    try {
      const data = await api.getMealPrepSchedule(planId);
      setSchedule(data);
    } catch (error) {
      console.error('Failed to load prep schedule:', error);
      Alert.alert('Error', 'Failed to load meal prep schedule');
    } finally {
      setLoading(false);
    }
  }

  async function toggleTaskComplete(taskId: number) {
    try {
      await api.completePrepTask(planId, taskId);
      loadPrepSchedule();
    } catch (error) {
      console.error('Failed to complete task:', error);
      Alert.alert('Error', 'Failed to update task');
    }
  }

  function renderTask(task: PrepTask) {
    return (
      <TouchableOpacity
        key={task.id}
        style={[styles.taskItem, task.completed && styles.taskItemCompleted]}
        onPress={() => toggleTaskComplete(task.id)}
      >
        <View style={styles.taskCheckbox}>
          {task.completed ? <Text style={styles.checkmark}>✓</Text> : null}
        </View>
        <View style={styles.taskContent}>
          <Text style={[styles.taskText, task.completed && styles.taskTextCompleted]}>
            {task.task}
          </Text>
          <Text style={styles.taskMeta}>
            {task.recipe_name} • {task.estimated_time_min} min
          </Text>
        </View>
        {task.estimated_time_min && (
          <View style={styles.taskTime}>
            <Text style={styles.taskTimeText}>{task.estimated_time_min}</Text>
            <Text style={styles.taskTimeLabel}>min</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  }

  function renderGroupedView() {
    if (!schedule) return null;

    const groups =
      viewMode === 'technique'
        ? schedule.grouped_by_technique
        : schedule.grouped_by_ingredient;

    return Object.entries(groups).map(([groupName, tasks]) => (
      <View key={groupName} style={styles.group}>
        <View style={styles.groupHeader}>
          <Text style={styles.groupTitle}>{groupName}</Text>
          <Text style={styles.groupCount}>
            {tasks.filter(t => !t.completed).length} / {tasks.length}
          </Text>
        </View>
        {tasks.map(task => renderTask(task))}
      </View>
    ));
  }

  function renderLinearView() {
    if (!schedule) return null;

    return schedule.tasks.map(task => renderTask(task));
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading prep tasks...</Text>
      </View>
    );
  }

  if (!schedule || schedule.tasks.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>No meal prep tasks found</Text>
        <Text style={styles.emptySubtext}>Create a meal plan to see batch cooking tasks</Text>
      </View>
    );
  }

  const completedCount = schedule.tasks.filter(t => t.completed).length;
  const totalCount = schedule.tasks.length;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{schedule.total_time_min}</Text>
            <Text style={styles.statLabel}>total minutes</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>
              {completedCount}/{totalCount}
            </Text>
            <Text style={styles.statLabel}>tasks done</Text>
          </View>
        </View>

        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress}%` }]} />
        </View>

        <View style={styles.viewModeSelector}>
          <TouchableOpacity
            style={[styles.viewModeBtn, viewMode === 'technique' && styles.viewModeBtnActive]}
            onPress={() => setViewMode('technique')}
          >
            <Text style={styles.viewModeBtnText}>By Technique</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.viewModeBtn, viewMode === 'ingredient' && styles.viewModeBtnActive]}
            onPress={() => setViewMode('ingredient')}
          >
            <Text style={styles.viewModeBtnText}>By Ingredient</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.viewModeBtn, viewMode === 'linear' && styles.viewModeBtnActive]}
            onPress={() => setViewMode('linear')}
          >
            <Text style={styles.viewModeBtnText}>Linear</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {viewMode === 'linear' ? renderLinearView() : renderGroupedView()}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#4CAF50',
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#e5e7eb',
    borderRadius: 4,
    marginBottom: 16,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  viewModeSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  viewModeBtn: {
    flex: 1,
    padding: 10,
    borderRadius: 8,
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    alignItems: 'center',
  },
  viewModeBtnActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  viewModeBtnText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#374151',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  group: {
    marginBottom: 24,
  },
  groupHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  groupTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  groupCount: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  taskItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 14,
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  taskItemCompleted: {
    backgroundColor: '#f9fafb',
    opacity: 0.6,
  },
  taskCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#4CAF50',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmark: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: '700',
  },
  taskContent: {
    flex: 1,
  },
  taskText: {
    fontSize: 15,
    color: '#111827',
    fontWeight: '500',
    marginBottom: 4,
  },
  taskTextCompleted: {
    textDecorationLine: 'line-through',
    color: '#6b7280',
  },
  taskMeta: {
    fontSize: 12,
    color: '#6b7280',
  },
  taskTime: {
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
  },
  taskTimeText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  taskTimeLabel: {
    fontSize: 10,
    color: '#6b7280',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 8,
  },
});
