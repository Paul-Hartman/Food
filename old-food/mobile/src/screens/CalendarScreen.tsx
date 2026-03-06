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

interface FamilyMember {
  id: number;
  name: string;
  avatar_emoji: string;
  color: string;
}

interface Meal {
  recipe_id: number;
  recipe_name: string;
  recipe_source: string;
  chef_member_id?: number;
}

interface CalendarEvent {
  id: number;
  title: string;
  start_datetime: string;
  color?: string;
}

interface DayData {
  date: string;
  meals: {
    breakfast?: Meal;
    lunch?: Meal;
    dinner?: Meal;
  };
  events: CalendarEvent[];
  busyness: {
    busyness_score: number;
    event_count: number;
  };
}

interface WeekData {
  days: DayData[];
}

interface Recipe {
  id: number;
  name: string;
  image_url?: string;
  prep_time_min?: number;
  cuisine?: string;
  source?: string;
}

const MEAL_ICONS = {
  breakfast: '☀️',
  lunch: '🌤️',
  dinner: '🌙',
  snack: '🍪',
};

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function CalendarScreen() {
  const [weekData, setWeekData] = useState<WeekData | null>(null);
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentWeekStart, setCurrentWeekStart] = useState(getWeekStart(new Date()));

  // Schedule Modal State
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedMealType, setSelectedMealType] = useState<'breakfast' | 'lunch' | 'dinner'>('breakfast');
  const [recipeSearch, setRecipeSearch] = useState('');
  const [searchResults, setSearchResults] = useState<Recipe[]>([]);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    loadWeekData();
  }, [currentWeekStart]);

  function getWeekStart(date: Date): Date {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
  }

  function formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  function changeWeek(direction: number) {
    const newStart = new Date(currentWeekStart);
    newStart.setDate(newStart.getDate() + direction * 7);
    setCurrentWeekStart(newStart);
  }

  function getDateDisplay(): string {
    const start = new Date(currentWeekStart);
    const end = new Date(start);
    end.setDate(end.getDate() + 6);

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const startMonth = months[start.getMonth()];
    const endMonth = months[end.getMonth()];

    if (startMonth === endMonth) {
      return `${startMonth} ${start.getDate()} - ${end.getDate()}, ${start.getFullYear()}`;
    }
    return `${startMonth} ${start.getDate()} - ${endMonth} ${end.getDate()}, ${start.getFullYear()}`;
  }

  async function loadWeekData() {
    setLoading(true);
    try {
      const startDate = formatDate(currentWeekStart);
      const [calendarData, membersData] = await Promise.all([
        api.getCalendarWeek(startDate),
        api.getFamilyMembers(),
      ]);

      setWeekData(calendarData);
      setFamilyMembers(membersData);
    } catch (error) {
      console.error('Failed to load calendar:', error);
      Alert.alert('Error', 'Failed to load calendar data');
    } finally {
      setLoading(false);
    }
  }

  function openScheduleModal(date: string, mealType: 'breakfast' | 'lunch' | 'dinner') {
    setSelectedDate(date);
    setSelectedMealType(mealType);
    setSelectedRecipe(null);
    setRecipeSearch('');
    setSearchResults([]);
    setScheduleModalVisible(true);
  }

  async function searchRecipes(query: string) {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const results = await api.searchRecipes(query);
      setSearchResults(results);
    } catch (error) {
      console.error('Failed to search recipes:', error);
    } finally {
      setSearching(false);
    }
  }

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchRecipes(recipeSearch);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [recipeSearch]);

  async function scheduleMeal() {
    if (!selectedRecipe) return;

    try {
      await api.scheduleMeal({
        recipe_id: selectedRecipe.id,
        recipe_source: selectedRecipe.source || 'local',
        recipe_name: selectedRecipe.name,
        meal_type: selectedMealType,
        scheduled_date: selectedDate,
      });

      setScheduleModalVisible(false);
      loadWeekData();
    } catch (error) {
      console.error('Failed to schedule meal:', error);
      Alert.alert('Error', 'Failed to schedule meal');
    }
  }

  async function scheduleQuickOption(optionName: string) {
    try {
      await api.scheduleMeal({
        recipe_id: 0,
        recipe_source: 'quick_entry',
        recipe_name: optionName,
        meal_type: selectedMealType,
        scheduled_date: selectedDate,
      });

      setScheduleModalVisible(false);
      loadWeekData();
    } catch (error) {
      console.error('Failed to schedule quick option:', error);
      Alert.alert('Error', 'Failed to schedule meal');
    }
  }

  function renderMealSlot(day: DayData, mealType: 'breakfast' | 'lunch' | 'dinner') {
    const meal = day.meals[mealType];
    const chef = meal?.chef_member_id ? familyMembers.find(m => m.id === meal.chef_member_id) : null;

    return (
      <TouchableOpacity
        key={mealType}
        style={[
          styles.mealSlot,
          meal ? styles.mealSlotFilled : styles.mealSlotEmpty,
          meal && chef && { backgroundColor: chef.color + '22' },
        ]}
        onPress={() => openScheduleModal(day.date, mealType)}
      >
        <Text style={styles.mealIcon}>{MEAL_ICONS[mealType]}</Text>
        {meal ? (
          <>
            <Text style={styles.mealName} numberOfLines={2}>
              {meal.recipe_name}
            </Text>
            {chef && (
              <View style={styles.chefBadge}>
                <Text style={[styles.chefAvatar, { backgroundColor: chef.color }]}>
                  {chef.avatar_emoji}
                </Text>
                <Text style={styles.chefName} numberOfLines={1}>
                  {chef.name}
                </Text>
              </View>
            )}
          </>
        ) : (
          <Text style={styles.mealLabel}>{mealType}</Text>
        )}
      </TouchableOpacity>
    );
  }

  function renderDay(day: DayData, index: number) {
    const dateObj = new Date(day.date);
    const dayName = DAYS[dateObj.getDay()];
    const dayNum = dateObj.getDate();
    const isToday = formatDate(new Date()) === day.date;

    const busynessClass = day.busyness.busyness_score <= 3 ? 'low' : day.busyness.busyness_score <= 6 ? 'medium' : 'high';
    const busynessColor = busynessClass === 'low' ? '#10b981' : busynessClass === 'medium' ? '#f59e0b' : '#ef4444';

    return (
      <View key={day.date} style={styles.dayColumn}>
        <View style={styles.dayHeader}>
          <View style={styles.dayHeaderLeft}>
            <Text style={styles.dayName}>
              {dayName} {dayNum}
            </Text>
            {isToday && <View style={styles.todayBadge}><Text style={styles.todayText}>Today</Text></View>}
          </View>
          {day.busyness.event_count > 0 && (
            <View style={[styles.busyBadge, { backgroundColor: busynessColor + '33' }]}>
              <Text style={[styles.busyText, { color: busynessColor }]}>
                {day.busyness.event_count} event{day.busyness.event_count > 1 ? 's' : ''}
              </Text>
            </View>
          )}
        </View>

        <View style={styles.dayContent}>
          <View style={styles.mealsRow}>
            {renderMealSlot(day, 'breakfast')}
            {renderMealSlot(day, 'lunch')}
            {renderMealSlot(day, 'dinner')}
          </View>

          {day.events.length > 0 && (
            <View style={styles.eventsList}>
              {day.events.slice(0, 3).map(event => (
                <View key={event.id} style={styles.eventItem}>
                  <View style={[styles.eventColor, { backgroundColor: event.color || '#6366f1' }]} />
                  <View style={styles.eventInfo}>
                    <Text style={styles.eventTitle} numberOfLines={1}>
                      {event.title}
                    </Text>
                    {event.start_datetime && (
                      <Text style={styles.eventTime}>
                        {new Date(event.start_datetime).toLocaleTimeString('en-US', {
                          hour: 'numeric',
                          minute: '2-digit',
                        })}
                      </Text>
                    )}
                  </View>
                </View>
              ))}
              {day.events.length > 3 && (
                <Text style={styles.moreEvents}>+{day.events.length - 3} more</Text>
              )}
            </View>
          )}

          {day.busyness.busyness_score >= 6 && !day.meals.dinner && (
            <View style={styles.suggestionBanner}>
              <Text style={styles.suggestionIcon}>⚡</Text>
              <Text style={styles.suggestionText}>Busy day! Try a quick 20-min meal</Text>
            </View>
          )}
        </View>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading calendar...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerNav}>
          <TouchableOpacity style={styles.navBtn} onPress={() => changeWeek(-1)}>
            <Text style={styles.navBtnText}>←</Text>
          </TouchableOpacity>
          <Text style={styles.dateDisplay}>{getDateDisplay()}</Text>
          <TouchableOpacity style={styles.navBtn} onPress={() => changeWeek(1)}>
            <Text style={styles.navBtnText}>→</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {weekData?.days.map((day, index) => renderDay(day, index))}
      </ScrollView>

      {/* Schedule Modal */}
      <Modal
        visible={scheduleModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setScheduleModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Schedule Meal</Text>
              <TouchableOpacity onPress={() => setScheduleModalVisible(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <View style={styles.mealTypeSelector}>
                {(['breakfast', 'lunch', 'dinner'] as const).map(type => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.mealTypeBtn,
                      selectedMealType === type && styles.mealTypeBtnSelected,
                    ]}
                    onPress={() => setSelectedMealType(type)}
                  >
                    <Text style={styles.mealTypeBtnText}>
                      {MEAL_ICONS[type]} {type.charAt(0).toUpperCase() + type.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TextInput
                style={styles.searchInput}
                placeholder="Search recipes..."
                value={recipeSearch}
                onChangeText={setRecipeSearch}
              />

              <ScrollView style={styles.recipeResults}>
                {searching ? (
                  <ActivityIndicator style={styles.searching} />
                ) : searchResults.length > 0 ? (
                  searchResults.map(recipe => (
                    <TouchableOpacity
                      key={recipe.id}
                      style={[
                        styles.recipeOption,
                        selectedRecipe?.id === recipe.id && styles.recipeOptionSelected,
                      ]}
                      onPress={() => setSelectedRecipe(recipe)}
                    >
                      <Text style={styles.recipeOptionName}>{recipe.name}</Text>
                      <Text style={styles.recipeOptionMeta}>
                        {recipe.prep_time_min ? `${recipe.prep_time_min} min` : ''}{' '}
                        {recipe.cuisine ? `• ${recipe.cuisine}` : ''}
                      </Text>
                    </TouchableOpacity>
                  ))
                ) : recipeSearch.length >= 2 ? (
                  <Text style={styles.noResults}>No recipes found</Text>
                ) : (
                  <Text style={styles.noResults}>Type to search recipes...</Text>
                )}
              </ScrollView>

              <View style={styles.quickOptions}>
                <Text style={styles.quickOptionsLabel}>Quick options:</Text>
                <View style={styles.quickOptionsButtons}>
                  <TouchableOpacity
                    style={styles.quickOptionBtn}
                    onPress={() => scheduleQuickOption('Eating Out')}
                  >
                    <Text>🍽️ Eating Out</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.quickOptionBtn}
                    onPress={() => scheduleQuickOption('Leftovers')}
                  >
                    <Text>🍲 Leftovers</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.quickOptionBtn}
                    onPress={() => scheduleQuickOption('Meal Prep')}
                  >
                    <Text>🥙 Meal Prep</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={styles.btnCancel}
                onPress={() => setScheduleModalVisible(false)}
              >
                <Text style={styles.btnCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btnSave, !selectedRecipe && styles.btnSaveDisabled]}
                onPress={scheduleMeal}
                disabled={!selectedRecipe}
              >
                <Text style={styles.btnSaveText}>Schedule Meal</Text>
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
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerNav: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  navBtn: {
    width: 36,
    height: 36,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    backgroundColor: '#fff',
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
    gap: 12,
  },
  dayColumn: {
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    overflow: 'hidden',
    marginBottom: 12,
  },
  dayHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f9fafb',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  dayHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dayName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  todayBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  todayText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
  },
  busyBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  busyText: {
    fontSize: 12,
    fontWeight: '500',
  },
  dayContent: {
    padding: 12,
  },
  mealsRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  mealSlot: {
    flex: 1,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 10,
    minHeight: 80,
    borderWidth: 2,
  },
  mealSlotEmpty: {
    borderStyle: 'dashed',
    borderColor: '#e5e7eb',
  },
  mealSlotFilled: {
    borderColor: 'transparent',
  },
  mealIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  mealLabel: {
    fontSize: 11,
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  mealName: {
    fontSize: 13,
    fontWeight: '500',
    marginTop: 6,
    lineHeight: 16,
  },
  chefBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 6,
  },
  chefAvatar: {
    width: 18,
    height: 18,
    borderRadius: 9,
    fontSize: 10,
    textAlign: 'center',
    lineHeight: 18,
  },
  chefName: {
    fontSize: 11,
    color: '#6b7280',
    flex: 1,
  },
  eventsList: {
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingTop: 10,
  },
  eventItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 8,
    backgroundColor: '#f9fafb',
    borderRadius: 6,
    marginBottom: 6,
  },
  eventColor: {
    width: 4,
    height: 24,
    borderRadius: 2,
  },
  eventInfo: {
    flex: 1,
  },
  eventTitle: {
    fontSize: 13,
    color: '#111827',
  },
  eventTime: {
    fontSize: 11,
    color: '#6b7280',
    marginTop: 2,
  },
  moreEvents: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  suggestionBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    borderRadius: 8,
    padding: 12,
    marginTop: 10,
  },
  suggestionIcon: {
    fontSize: 18,
  },
  suggestionText: {
    fontSize: 13,
    color: '#4f46e5',
    flex: 1,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modal: {
    backgroundColor: '#fff',
    borderRadius: 16,
    width: '100%',
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
  mealTypeSelector: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  mealTypeBtn: {
    flex: 1,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    backgroundColor: '#f9fafb',
    alignItems: 'center',
  },
  mealTypeBtnSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  mealTypeBtnText: {
    fontSize: 13,
  },
  searchInput: {
    width: '100%',
    padding: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    backgroundColor: '#f9fafb',
    fontSize: 15,
    marginBottom: 16,
  },
  recipeResults: {
    maxHeight: 250,
  },
  searching: {
    padding: 20,
  },
  recipeOption: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: 'transparent',
    marginBottom: 8,
    backgroundColor: '#f9fafb',
  },
  recipeOptionSelected: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  recipeOptionName: {
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 4,
  },
  recipeOptionMeta: {
    fontSize: 12,
    color: '#6b7280',
  },
  noResults: {
    textAlign: 'center',
    color: '#6b7280',
    padding: 20,
  },
  quickOptions: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  quickOptionsLabel: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 12,
  },
  quickOptionsButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  quickOptionBtn: {
    padding: 10,
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    flex: 1,
    alignItems: 'center',
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
  btnSaveDisabled: {
    opacity: 0.5,
  },
  btnSaveText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
