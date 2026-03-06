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

interface GameDashboard {
  member: {
    id: number;
    name: string;
    avatar_emoji: string;
    level: number;
    xp: number;
    xp_to_next_level: number;
  };
  needs: {
    hunger: number;
    energy: number;
    health: number;
  };
  skills: Array<{
    skill_name: string;
    level: number;
    progress: number;
  }>;
  recent_achievements: Array<{
    name: string;
    description: string;
    icon: string;
    unlocked_at: string;
  }>;
  recipe_collection_stats: {
    total_recipes: number;
    common: number;
    rare: number;
    epic: number;
    legendary: number;
  };
}

export default function GameScreen() {
  const [familyMembers, setFamilyMembers] = useState<any[]>([]);
  const [selectedMemberId, setSelectedMemberId] = useState<number | null>(null);
  const [dashboard, setDashboard] = useState<GameDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFamilyMembers();
  }, []);

  useEffect(() => {
    if (selectedMemberId) {
      loadDashboard();
    }
  }, [selectedMemberId]);

  async function loadFamilyMembers() {
    try {
      const members = await api.getFamilyMembers();
      setFamilyMembers(members);
      if (members.length > 0 && !selectedMemberId) {
        setSelectedMemberId(members[0].id);
      }
    } catch (error) {
      console.error('Failed to load family members:', error);
      Alert.alert('Error', 'Failed to load family members');
    } finally {
      setLoading(false);
    }
  }

  async function loadDashboard() {
    if (!selectedMemberId) return;

    setLoading(true);
    try {
      const data = await api.getGameDashboard(selectedMemberId);
      setDashboard(data);
    } catch (error) {
      console.error('Failed to load game dashboard:', error);
      Alert.alert('Error', 'Failed to load game dashboard');
    } finally {
      setLoading(false);
    }
  }

  function getNeedColor(value: number): string {
    if (value >= 70) return '#10b981';
    if (value >= 40) return '#f59e0b';
    return '#ef4444';
  }

  function getRarityColor(rarity: string): string {
    switch (rarity.toLowerCase()) {
      case 'common': return '#9ca3af';
      case 'rare': return '#3b82f6';
      case 'epic': return '#8b5cf6';
      case 'legendary': return '#f59e0b';
      default: return '#6b7280';
    }
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  if (familyMembers.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>Add family members to start Kitchen Quest</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Member Selector */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.memberSelector}>
        {familyMembers.map(member => (
          <TouchableOpacity
            key={member.id}
            style={[
              styles.memberBtn,
              selectedMemberId === member.id && styles.memberBtnSelected,
            ]}
            onPress={() => setSelectedMemberId(member.id)}
          >
            <Text style={styles.memberBtnEmoji}>{member.avatar_emoji}</Text>
            <Text style={styles.memberBtnName}>{member.name}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {dashboard && (
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          {/* Level & XP */}
          <View style={styles.card}>
            <View style={styles.levelHeader}>
              <Text style={styles.memberEmoji}>{dashboard.member.avatar_emoji}</Text>
              <View style={styles.levelInfo}>
                <Text style={styles.memberName}>{dashboard.member.name}</Text>
                <Text style={styles.levelText}>Level {dashboard.member.level}</Text>
              </View>
            </View>
            <View style={styles.xpBar}>
              <View
                style={[
                  styles.xpFill,
                  {
                    width: `${
                      (dashboard.member.xp / dashboard.member.xp_to_next_level) * 100
                    }%`,
                  },
                ]}
              />
            </View>
            <Text style={styles.xpText}>
              {dashboard.member.xp} / {dashboard.member.xp_to_next_level} XP
            </Text>
          </View>

          {/* Needs */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>👤 Needs</Text>
            {Object.entries(dashboard.needs).map(([need, value]) => (
              <View key={need} style={styles.needRow}>
                <Text style={styles.needLabel}>{need}</Text>
                <View style={styles.needBar}>
                  <View
                    style={[
                      styles.needFill,
                      { width: `${value}%`, backgroundColor: getNeedColor(value) },
                    ]}
                  />
                </View>
                <Text style={styles.needValue}>{value}%</Text>
              </View>
            ))}
          </View>

          {/* Skills */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>🔪 Cooking Skills</Text>
            {dashboard.skills.slice(0, 5).map((skill, idx) => (
              <View key={idx} style={styles.skillRow}>
                <Text style={styles.skillName}>{skill.skill_name}</Text>
                <Text style={styles.skillLevel}>Lv {skill.level}</Text>
                <View style={styles.skillBar}>
                  <View style={[styles.skillFill, { width: `${skill.progress}%` }]} />
                </View>
              </View>
            ))}
          </View>

          {/* Recipe Collection */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>📖 Recipe Collection</Text>
            <Text style={styles.collectionTotal}>
              {dashboard.recipe_collection_stats.total_recipes} recipes discovered
            </Text>
            <View style={styles.rarityGrid}>
              {['common', 'rare', 'epic', 'legendary'].map(rarity => {
                const count = dashboard.recipe_collection_stats[
                  rarity as keyof typeof dashboard.recipe_collection_stats
                ] as number;
                return (
                  <View key={rarity} style={styles.rarityCard}>
                    <Text
                      style={[
                        styles.rarityCount,
                        { color: getRarityColor(rarity) },
                      ]}
                    >
                      {count}
                    </Text>
                    <Text style={styles.rarityLabel}>{rarity}</Text>
                  </View>
                );
              })}
            </View>
          </View>

          {/* Achievements */}
          {dashboard.recent_achievements.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>🏆 Recent Achievements</Text>
              {dashboard.recent_achievements.map((achievement, idx) => (
                <View key={idx} style={styles.achievementRow}>
                  <Text style={styles.achievementIcon}>{achievement.icon}</Text>
                  <View style={styles.achievementInfo}>
                    <Text style={styles.achievementName}>{achievement.name}</Text>
                    <Text style={styles.achievementDesc}>{achievement.description}</Text>
                  </View>
                </View>
              ))}
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  memberSelector: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    paddingHorizontal: 16,
    paddingVertical: 12,
    maxHeight: 90,
  },
  memberBtn: {
    alignItems: 'center',
    marginRight: 16,
    padding: 8,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'transparent',
    minWidth: 70,
  },
  memberBtnSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  memberBtnEmoji: {
    fontSize: 32,
    marginBottom: 4,
  },
  memberBtnName: {
    fontSize: 12,
    fontWeight: '500',
    color: '#374151',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
  },
  levelHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  memberEmoji: {
    fontSize: 48,
    marginRight: 16,
  },
  levelInfo: {
    flex: 1,
  },
  memberName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  levelText: {
    fontSize: 16,
    color: '#6b7280',
    fontWeight: '600',
  },
  xpBar: {
    height: 12,
    backgroundColor: '#e5e7eb',
    borderRadius: 6,
    overflow: 'hidden',
    marginBottom: 8,
  },
  xpFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  xpText: {
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
  },
  needRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  needLabel: {
    fontSize: 14,
    color: '#374151',
    textTransform: 'capitalize',
    width: 70,
  },
  needBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#e5e7eb',
    borderRadius: 4,
    overflow: 'hidden',
    marginHorizontal: 12,
  },
  needFill: {
    height: '100%',
  },
  needValue: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '600',
    width: 45,
    textAlign: 'right',
  },
  skillRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  skillName: {
    fontSize: 14,
    color: '#374151',
    flex: 1,
  },
  skillLevel: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '600',
    marginRight: 12,
  },
  skillBar: {
    width: 60,
    height: 6,
    backgroundColor: '#e5e7eb',
    borderRadius: 3,
    overflow: 'hidden',
  },
  skillFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  collectionTotal: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 16,
  },
  rarityGrid: {
    flexDirection: 'row',
    gap: 8,
  },
  rarityCard: {
    flex: 1,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  rarityCount: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  rarityLabel: {
    fontSize: 11,
    color: '#6b7280',
    textTransform: 'capitalize',
  },
  achievementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
  },
  achievementIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  achievementInfo: {
    flex: 1,
  },
  achievementName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 2,
  },
  achievementDesc: {
    fontSize: 12,
    color: '#6b7280',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 60,
  },
});
