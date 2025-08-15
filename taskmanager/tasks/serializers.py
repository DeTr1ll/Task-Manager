"""Serializers for the tasks app."""

from rest_framework import serializers

from .models import Task, Tag


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model with support for tags.

    Fields:
        - tags: PrimaryKeyRelatedField for existing tags.
        - tags_names: List of tag names to create or associate with task.
    """

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    tags_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
    )

    class Meta:
        """Meta options for TaskSerializer."""
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'due_date',
            'tags',
            'tags_names',
        ]

    def create(self, validated_data):
        """
        Create a new Task instance.

        If 'tags_names' are provided, create new tags if they don't exist
        and associate them with the task.
        """
        tags_names = validated_data.pop('tags_names', [])
        task = super().create(validated_data)

        for name in tags_names:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                user=self.context['request'].user,
            )
            task.tags.add(tag)

        return task

    def update(self, instance, validated_data):
        """
        Update an existing Task instance.

        If 'tags_names' are provided, clear existing tags and
        associate the new ones, creating tags as needed.
        """
        tags_names = validated_data.pop('tags_names', [])
        task = super().update(instance, validated_data)

        if tags_names:
            task.tags.clear()
            for name in tags_names:
                tag, _ = Tag.objects.get_or_create(
                    name=name,
                    user=self.context['request'].user,
                )
                task.tags.add(tag)

        return task
