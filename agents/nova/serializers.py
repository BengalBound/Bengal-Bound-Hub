from rest_framework import serializers
from .models import DataSource, DataQuery


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")


class DataQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataQuery
        fields = "__all__"
        read_only_fields = ("id", "business", "generated_sql", "results_preview", "status", "created_at", "updated_at")
