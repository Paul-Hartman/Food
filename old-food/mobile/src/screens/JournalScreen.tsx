import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { api } from '../services/api';

interface JournalEntry {
  id: number;
  date: string;
  meal_type?: string;
  content: string;
  mood?: string;
  created_at: string;
}

interface DailyJournal {
  date: string;
  entries: JournalEntry[];
  auto_entries: string[];
}

const MOOD_EMOJIS = ['😊', '😐', '😔', '🤩', '😴'];
const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'];

export default function JournalScreen() {
  const [journal, setJournal] = useState<DailyJournal | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  // Form state
  const [content, setContent] = useState('');
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  const [selectedMealType, setSelectedMealType] = useState<string | null>(null);

  useEffect(() => {
    loadJournal();
  }, [selectedDate]);

  async function loadJournal() {
    setLoading(true);
    try {
      const data =
        selectedDate === new Date().toISOString().split('T')[0]
          ? await api.getJournalToday()
          : await api.getJournalByDate(selectedDate);
      setJournal(data);
    } catch (error) {
      console.error('Failed to load journal:', error);
      Alert.alert('Error', 'Failed to load journal');
    } finally {
      setLoading(false);
    }
  }

  function openAddEntryModal() {
    setContent('');
    setSelectedMood(null);
    setSelectedMealType(null);
    setModalVisible(true);
  }

  async function saveEntry() {
    if (!content.trim()) {
      Alert.alert('Error', 'Please write something');
      return;
    }

    try {
      await api.createJournalEntry({
        date: selectedDate,
        content: content.trim(),
        mood: selectedMood || undefined,
        meal_type: selectedMealType || undefined,
      });
      setModalVisible(false);
      loadJournal();
    } catch (error) {
      console.error('Failed to save entry:', error);
      Alert.alert('Error', 'Failed to save journal entry');
    }
  }

  function changeDate(days: number) {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + days);
    setSelectedDate(newDate.toISOString().split('T')[0]);
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (dateStr === today.toISOString().split('T')[0]) return 'Today';
    if (dateStr === yesterday.toISOString().split('T')[0]) return 'Yesterday';

    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading journal...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.navBtn} onPress={() => changeDate(-1)}>
          <Text style={styles.navBtnText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.dateDisplay}>{formatDate(selectedDate)}</Text>
        <TouchableOpacity style={styles.navBtn} onPress={() => changeDate(1)}>
          <Text style={styles.navBtnText}>→</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Manual Entries */}
        {journal?.entries && journal.entries.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>📝 Your Entries</Text>
            {journal.entries.map(entry => (
              <View key={entry.id} style={styles.entryCard}>
                <View style={styles.entryHeader}>
                  {entry.mood && <Text style={styles.entryMood}>{entry.mood}</Text>}
                  {entry.meal_type && (
                    <Text style={styles.entryMealType}>{entry.meal_type}</Text>
                  )}
                  <Text style={styles.entryTime}>
                    {new Date(entry.created_at).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                    })}
                  </Text>
                </View>
                <Text style={styles.entryContent}>{entry.content}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Auto-generated Entries */}
        {journal?.auto_entries && journal.auto_entries.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>🤖 Auto-Generated</Text>
            {journal.auto_entries.map((entry, idx) => (
              <View key={idx} style={styles.autoEntryCard}>
                <Text style={styles.autoEntryText}>{entry}</Text>
              </View>
            ))}
          </View>
        )}

        {(!journal?.entries || journal.entries.length === 0) &&
          (!journal?.auto_entries || journal.auto_entries.length === 0) && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>📖</Text>
              <Text style={styles.emptyText}>No journal entries for this day</Text>
              <Text style={styles.emptySubtext}>
                Write about your meals and cooking experiences
              </Text>
            </View>
          )}
      </ScrollView>

      <TouchableOpacity style={styles.fab} onPress={openAddEntryModal}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>

      {/* Add Entry Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>New Journal Entry</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <Text style={styles.inputLabel}>How are you feeling?</Text>
              <View style={styles.moodSelector}>
                {MOOD_EMOJIS.map(mood => (
                  <TouchableOpacity
                    key={mood}
                    style={[
                      styles.moodBtn,
                      selectedMood === mood && styles.moodBtnSelected,
                    ]}
                    onPress={() => setSelectedMood(mood)}
                  >
                    <Text style={styles.moodEmoji}>{mood}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.inputLabel}>Related to meal?</Text>
              <View style={styles.mealTypeSelector}>
                {MEAL_TYPES.map(type => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.mealTypeBtn,
                      selectedMealType === type && styles.mealTypeBtnSelected,
                    ]}
                    onPress={() => setSelectedMealType(type)}
                  >
                    <Text style={styles.mealTypeBtnText}>{type}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.inputLabel}>What's on your mind?</Text>
              <TextInput
                style={styles.textArea}
                placeholder="Write about your meal, cooking experience, or how you're feeling..."
                value={content}
                onChangeText={setContent}
                multiline
                numberOfLines={6}
                textAlignVertical="top"
              />
            </View>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={styles.btnCancel}
                onPress={() => setModalVisible(false)}
              >
                <Text style={styles.btnCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.btnSave} onPress={saveEntry}>
                <Text style={styles.btnSaveText}>Save</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  navBtn: {
    width: 36,
    height: 36,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    alignItems: 'center',
    justifyContent: 'center',
  },
  navBtnText: {
    fontSize: 18,
    color: '#374151',
  },
  dateDisplay: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  entryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  entryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  entryMood: {
    fontSize: 20,
  },
  entryMealType: {
    fontSize: 12,
    color: '#6b7280',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    textTransform: 'capitalize',
  },
  entryTime: {
    fontSize: 12,
    color: '#9ca3af',
    marginLeft: 'auto',
  },
  entryContent: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 22,
  },
  autoEntryCard: {
    backgroundColor: '#fef3c7',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#fbbf24',
  },
  autoEntryText: {
    fontSize: 14,
    color: '#92400e',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 60,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#4CAF50',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  fabText: {
    fontSize: 32,
    color: '#fff',
    fontWeight: '300',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  modal: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  modalClose: {
    fontSize: 24,
    color: '#6b7280',
  },
  modalBody: {
    padding: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    marginTop: 16,
  },
  moodSelector: {
    flexDirection: 'row',
    gap: 12,
  },
  moodBtn: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    alignItems: 'center',
    justifyContent: 'center',
  },
  moodBtnSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  moodEmoji: {
    fontSize: 28,
  },
  mealTypeSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  mealTypeBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    backgroundColor: '#f9fafb',
  },
  mealTypeBtnSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  mealTypeBtnText: {
    fontSize: 13,
    color: '#374151',
    textTransform: 'capitalize',
  },
  textArea: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    backgroundColor: '#f9fafb',
    minHeight: 120,
  },
  modalFooter: {
    flexDirection: 'row',
    gap: 12,
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  btnCancel: {
    flex: 1,
    padding: 14,
    borderRadius: 8,
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    alignItems: 'center',
  },
  btnCancelText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  btnSave: {
    flex: 1,
    padding: 14,
    borderRadius: 8,
    backgroundColor: '#4CAF50',
    alignItems: 'center',
  },
  btnSaveText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
