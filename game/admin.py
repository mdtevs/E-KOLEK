from django.contrib import admin
from .models import Question, Choice, WasteCategory, WasteItem, GameSession

# Register your models here.

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ['text']

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct']
    list_filter = ['is_correct', 'question']

@admin.register(WasteCategory)
class WasteCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_hex', 'icon_name', 'created_at']
    list_filter = ['created_at']

@admin.register(WasteItem)
class WasteItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'emoji', 'category', 'points', 'difficulty_level', 'is_active']
    list_filter = ['category', 'difficulty_level', 'is_active']
    search_fields = ['name']

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'score', 'accuracy', 'completed_at']
    list_filter = ['completed_at']
    readonly_fields = ['completed_at']
