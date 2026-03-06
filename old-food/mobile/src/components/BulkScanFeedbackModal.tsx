import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  TextInput,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { api } from '../services/api';

interface BulkScanFeedbackModalProps {
  visible: boolean;
  onClose: () => void;
  itemCount: number;
  sessionId?: string;
}

export default function BulkScanFeedbackModal({
  visible,
  onClose,
  itemCount,
  sessionId,
}: BulkScanFeedbackModalProps) {
  const [satisfaction, setSatisfaction] = useState<number>(0);
  const [whatWorkedWell, setWhatWorkedWell] = useState('');
  const [whatCouldImprove, setWhatCouldImprove] = useState('');
  const [bugDescription, setBugDescription] = useState('');
  const [wouldRecommend, setWouldRecommend] = useState<boolean | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (satisfaction === 0) {
      Alert.alert('Missing Rating', 'Please select a satisfaction rating (1-5 stars)');
      return;
    }

    if (wouldRecommend === null) {
      Alert.alert('Missing Answer', 'Please answer if you would recommend this feature');
      return;
    }

    setSubmitting(true);
    try {
      await api.submitFeedback({
        sessionId,
        satisfaction,
        whatWorkedWell: whatWorkedWell.trim(),
        whatCouldImprove: whatCouldImprove.trim(),
        bugDescription: bugDescription.trim(),
        wouldRecommend,
        context: {
          feature: 'bulk_scan',
          itemCount,
        },
      });

      Alert.alert('Thanks!', 'Your feedback helps us improve the app!', [
        {
          text: 'OK',
          onPress: () => {
            resetForm();
            onClose();
          },
        },
      ]);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      Alert.alert('Error', 'Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setSatisfaction(0);
    setWhatWorkedWell('');
    setWhatCouldImprove('');
    setBugDescription('');
    setWouldRecommend(null);
  };

  const handleSkip = () => {
    resetForm();
    onClose();
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={handleSkip}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Header */}
            <Text style={styles.title}>How was your bulk scan?</Text>
            <Text style={styles.subtitle}>You scanned {itemCount} items</Text>

            {/* Star rating */}
            <Text style={styles.sectionLabel}>Overall satisfaction</Text>
            <View style={styles.starRow}>
              {[1, 2, 3, 4, 5].map((star) => (
                <TouchableOpacity
                  key={star}
                  onPress={() => setSatisfaction(star)}
                  style={styles.starButton}
                >
                  <Text style={[styles.star, satisfaction >= star && styles.starActive]}>
                    ★
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* What worked well */}
            <Text style={styles.sectionLabel}>What worked well?</Text>
            <TextInput
              style={styles.textArea}
              value={whatWorkedWell}
              onChangeText={setWhatWorkedWell}
              placeholder="E.g., Fast scanning, easy interface..."
              placeholderTextColor="#999"
              multiline
              maxLength={200}
            />

            {/* What could improve */}
            <Text style={styles.sectionLabel}>What could be better?</Text>
            <TextInput
              style={styles.textArea}
              value={whatCouldImprove}
              onChangeText={setWhatCouldImprove}
              placeholder="E.g., Better error handling, clearer feedback..."
              placeholderTextColor="#999"
              multiline
              maxLength={200}
            />

            {/* Bugs (optional) */}
            <Text style={styles.sectionLabel}>Any bugs? (optional)</Text>
            <TextInput
              style={styles.textArea}
              value={bugDescription}
              onChangeText={setBugDescription}
              placeholder="Describe any issues you encountered..."
              placeholderTextColor="#999"
              multiline
              maxLength={200}
            />

            {/* Would recommend */}
            <Text style={styles.sectionLabel}>Would you recommend this feature?</Text>
            <View style={styles.recommendRow}>
              <TouchableOpacity
                style={[
                  styles.recommendButton,
                  wouldRecommend === true && styles.recommendButtonActive,
                ]}
                onPress={() => setWouldRecommend(true)}
              >
                <Text
                  style={[
                    styles.recommendText,
                    wouldRecommend === true && styles.recommendTextActive,
                  ]}
                >
                  👍 Yes
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.recommendButton,
                  wouldRecommend === false && styles.recommendButtonActive,
                ]}
                onPress={() => setWouldRecommend(false)}
              >
                <Text
                  style={[
                    styles.recommendText,
                    wouldRecommend === false && styles.recommendTextActive,
                  ]}
                >
                  👎 No
                </Text>
              </TouchableOpacity>
            </View>

            {/* Action buttons */}
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.actionButton, styles.skipButton]}
                onPress={handleSkip}
                disabled={submitting}
              >
                <Text style={styles.skipButtonText}>Skip</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionButton, styles.submitButton]}
                onPress={handleSubmit}
                disabled={submitting}
              >
                <Text style={styles.submitButtonText}>
                  {submitting ? 'Submitting...' : 'Submit Feedback'}
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    maxHeight: '90%',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111',
    marginBottom: 4,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 24,
    textAlign: 'center',
  },
  sectionLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  starRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 8,
  },
  starButton: {
    padding: 4,
  },
  star: {
    fontSize: 40,
    color: '#ddd',
  },
  starActive: {
    color: '#FFD700',
  },
  textArea: {
    backgroundColor: '#f9f9f9',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#333',
    minHeight: 70,
    textAlignVertical: 'top',
  },
  recommendRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 8,
  },
  recommendButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#ddd',
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  recommendButtonActive: {
    borderColor: '#4CAF50',
    backgroundColor: '#E8F5E9',
  },
  recommendText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  recommendTextActive: {
    color: '#4CAF50',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  skipButton: {
    backgroundColor: '#f5f5f5',
  },
  submitButton: {
    backgroundColor: '#4CAF50',
  },
  skipButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
  },
});
