import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  TextInput,
  StyleSheet,
  Alert,
} from 'react-native';
import { api } from '../services/api';

interface ErrorReportButtonProps {
  screen: string;
  errorType?: string;
  errorMessage?: string;
  barcode?: string;
  context?: any;
  visible?: boolean;
  onDismiss?: () => void;
}

export default function ErrorReportButton({
  screen,
  errorType,
  errorMessage,
  barcode,
  context,
  visible = false,
  onDismiss,
}: ErrorReportButtonProps) {
  const [showButton, setShowButton] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [userNote, setUserNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Show button when visible prop changes to true
    if (visible) {
      setShowButton(true);
      // Auto-hide after 10 seconds if not interacted with
      const timer = setTimeout(() => {
        setShowButton(false);
        if (onDismiss) onDismiss();
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [visible]);

  const handleReport = async () => {
    setSubmitting(true);
    try {
      await api.flagBug({
        screen,
        description: userNote || errorMessage || 'User reported an error',
        severity: 'medium',
        errorType: errorType || 'unknown',
        barcode,
        context,
        source: 'error_report_button',
        timestamp: new Date().toISOString(),
      });

      setShowModal(false);
      setShowButton(false);
      setUserNote('');

      Alert.alert('Thanks!', 'Error report submitted successfully.', [{ text: 'OK' }]);

      if (onDismiss) onDismiss();
    } catch (error) {
      console.error('Failed to submit error report:', error);
      Alert.alert('Error', 'Failed to submit report. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    setShowModal(false);
    setShowButton(false);
    setUserNote('');
    if (onDismiss) onDismiss();
  };

  if (!showButton) return null;

  return (
    <>
      {/* Floating button */}
      <TouchableOpacity
        style={styles.floatingButton}
        onPress={() => setShowModal(true)}
      >
        <Text style={styles.buttonIcon}>🐛</Text>
        <Text style={styles.buttonText}>Report Error</Text>
      </TouchableOpacity>

      {/* Report modal */}
      <Modal
        visible={showModal}
        transparent
        animationType="fade"
        onRequestClose={handleCancel}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Report Error</Text>

            {/* Pre-filled context */}
            <View style={styles.contextBox}>
              <Text style={styles.contextLabel}>Screen:</Text>
              <Text style={styles.contextValue}>{screen}</Text>
              {errorType && (
                <>
                  <Text style={styles.contextLabel}>Error Type:</Text>
                  <Text style={styles.contextValue}>{errorType}</Text>
                </>
              )}
              {barcode && (
                <>
                  <Text style={styles.contextLabel}>Barcode:</Text>
                  <Text style={styles.contextValue}>{barcode}</Text>
                </>
              )}
              {errorMessage && (
                <>
                  <Text style={styles.contextLabel}>Error:</Text>
                  <Text style={styles.contextValue}>{errorMessage}</Text>
                </>
              )}
            </View>

            {/* User note */}
            <Text style={styles.inputLabel}>Additional notes (optional):</Text>
            <TextInput
              style={styles.textInput}
              value={userNote}
              onChangeText={setUserNote}
              placeholder="Describe what happened..."
              placeholderTextColor="#999"
              multiline
              numberOfLines={3}
              maxLength={200}
            />

            {/* Action buttons */}
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.actionButton, styles.cancelButton]}
                onPress={handleCancel}
                disabled={submitting}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionButton, styles.submitButton]}
                onPress={handleReport}
                disabled={submitting}
              >
                <Text style={styles.submitButtonText}>
                  {submitting ? 'Submitting...' : 'Submit'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  floatingButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    backgroundColor: 'rgba(239, 68, 68, 0.9)',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    zIndex: 1000,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  buttonIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111',
    marginBottom: 16,
    textAlign: 'center',
  },
  contextBox: {
    backgroundColor: '#f5f5f5',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  contextLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginTop: 4,
  },
  contextValue: {
    fontSize: 13,
    color: '#333',
    marginBottom: 4,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#f9f9f9',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#333',
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: 20,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#f5f5f5',
  },
  submitButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#666',
  },
  submitButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
});
