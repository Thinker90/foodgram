from rest_framework import status
from rest_framework.response import Response


class SubscriptionsManagerMixin:
    def add_subscribe(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_subscribe(self, model, filter_set, message: dict):
        subscription = model.objects.filter(**filter_set).first()
        if subscription:
            subscription.delete()
            return Response({'success': message['success']},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'message': message['error']},
                status=status.HTTP_400_BAD_REQUEST)
