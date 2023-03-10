from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from account_app.permissions import OwnerOrRead
from .serializers import ArticleSerializer, LikeSerializer, CommentSerializer
from .models import Article, IpAddress, Like, Comment


# class ArticleViewSet(ModelViewSet):
#     queryset = Article.objects.filter(allowing=True)
#     serializer_class = ArticleSerializer
#
#     def get_permissions(self):
#         if self.action in ['update', 'create', 'destroy', 'partial_update']:
#             permission_classes = [IsAdminUser]
#         else:
#             permission_classes = [OwnerOrRead]
#         return [permission() for permission in permission_classes]


class ArticlesView(APIView):
    def get(self, request):
        articles = Article.objects.filter(allowing=True)
        ser = ArticleSerializer(instance=articles, many=True, context={'request': request})
        return Response(data=ser.data)


class ArticleDetailView(APIView):
    def get(self, request, id, slug):
        article = Article.objects.get(id=id, slug=slug, allowing=True)
        ser = ArticleSerializer(instance=article, context={'request': request})
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        try:
            ip_address = IpAddress.objects.get(ip_address=ip)
        except IpAddress.DoesNotExist:
            ip_address = IpAddress(ip_address=ip)
            ip_address.save()
        if ip_address not in article.hits.all():
            article.hits.add(ip_address)
        return Response(ser.data)


class CreateArticleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            if request.user.is_authenticated:
                serializer.validated_data['user'] = request.user
            serializer.save()
            return Response({"response": "created"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateArticleView(APIView):
    permission_classes = [IsAdminUser, IsAuthenticated, OwnerOrRead]

    def put(self, request, id):
        instance = Article.objects.get(id=id)
        self.check_object_permissions(request, instance)
        serializer = ArticleSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.update(instance=instance, validated_data=serializer.validated_data)
            return Response({"response": "updated"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteArticleView(APIView):
    permission_classes = [IsAdminUser, IsAuthenticated, OwnerOrRead]

    def delete(self, request, id):
        instance = Article.objects.get(id=id)
        instance.delete()
        return Response({"response": "deleted"}, status=status.HTTP_200_OK)


class LikeListCreate(APIView):

    def get(self, request, id):
        article_likes = Article.objects.get(id=id).likes.all()
        serializer = LikeSerializer(instance=article_likes, many=True)
        return Response(serializer.data)

    def post(self, request, id):
        article = Article.objects.get(id=id)
        check = Like.objects.filter(user_id=request.user.id, article_id=article.id)
        if check.exists():
            check.delete()
            return Response({
                "message": "unliked"
            })
        new_like = Like.objects.create(user_id=request.user.id, article_id=article.id)
        new_like.save()
        return Response({"response": "liked"}, status=status.HTTP_201_CREATED)

class CommentCreate(APIView):
    def get(self, request, id):
        article_comments = Article.objects.get(id=id).comments.all()
        serializer = CommentSerializer(instance=article_comments, many=True)
        return Response(serializer.data)

    def post(self, request, id):
        article = Article.objects.get(id=id)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['article'] = article
            serializer.save()
            return Response({"response": "commented"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def post(self, request, id):
    #     article = Article.objects.get(id=id)
    #     return Response({
    #         "message": "commented"
    #     })
    #     new_comment = Comment.objects.create(article_id=article.id)
    #     new_like.save()
    #     return Response({"response": "liked"}, status=status.HTTP_201_CREATED)
