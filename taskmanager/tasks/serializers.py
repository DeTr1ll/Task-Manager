from rest_framework import serializers

from .models import Task, Tag


class TaskSerializer(serializers.ModelSerializer):
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
