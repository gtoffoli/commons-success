from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required

from rest_framework import routers, serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from actstream.models import Action

import commons
from commons.models import User, Project, OER, OerDocument, LearningPath, Folder, FolderDocument
from commons.models import site_member_users
from commons.models import PROJECT_OPEN, PUBLISHED
from commons.user_spaces import project_tree_as_list, folder_tree_as_list, tree_to_list, filter_documents
from commons.api import router, make_contenttype_dict
from commons.api import UserProjectSerializer

root = 'success-erasmus'

class UserSerializer(commons.api.UserSerializer):
    class Meta:
        model = User
        # exclude = ('user_permissions',)
        # fields = ('id', 'username', 'first_name', 'last_name', 'email', 'date_joined', 'groups',)
        # depth = 1
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'date_joined',)
 
    # groups = UserProjectSerializer(many=True)

    # bypass method re-definition in parent class
    def to_representation(self, instance):
        representation = serializers.HyperlinkedModelSerializer.to_representation(self, instance)
        return representation

class FilteredUserViewSet(commons.api.UserViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    serializer_class = UserSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'username', 'email', 'first_name', 'last_name')

    def get_queryset(self):
        queryset = site_member_users()
        return queryset

    def list(self, request):
        if not request.user.is_authenticated or not request.user in site_member_users():
            return HttpResponse(403, 'Permission Denied')
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        data = serializer.data
        return JsonResponse(data, safe=False)

class ProjectSerializer(commons.api.ProjectSerializer):

    class Meta:
        model = Project
        # fields = ('id', 'local_path', 'name', 'project_type', 'info', 'created')
        fields = ('id', 'local_path', 'name', 'project_type',)
    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    project_type = serializers.ReadOnlyField(source='get_type_name')

""" recursively computes the project tree with root in the given project,
    including all project and community types """
def project_tree_as_dict(project, request):
    serializer = ProjectSerializer(project, context={'request': request})
    tree = serializer.data
    children = project.get_children(states=[PROJECT_OPEN], all_proj_type_public=True)
    if children:
        tree['children'] = [project_tree_as_dict(child, request) for child in children]
    return tree

class FilteredProjectViewSet(commons.api.ProjectViewSet):
    serializer_class = ProjectSerializer
    http_method_names = ['get', 'head', 'options',]

    def list(self, request):
        community = Project.objects.get(slug=root)
        data = project_tree_as_dict(community, request)
        return JsonResponse(data)

class FolderSerializer(commons.api.FolderSerializer):
    class Meta:
        model = Folder
        fields = ('id', 'title', 'project_name', 'project_id', 'parent_id', 'n_documents',)

    project_name = serializers.SerializerMethodField()
    def get_project_name(self, obj):
        return obj.get_project().name

    n_documents = serializers.SerializerMethodField()
    def get_n_documents(self, obj):
        return obj.documents.all().count()

class FilteredFolderViewSet(commons.api.FolderViewSet):
    """ API endpoint for listing project folders. """
    serializer_class = FolderSerializer
    http_method_names = ['get', 'head', 'options',]

    def list(self, request):
        community = Project.objects.get(slug=root)
        projects = tree_to_list(project_tree_as_list(community))
        folders = []
        for project in projects:
            folder = project.get_folder()
            if folder:
                folders.extend(tree_to_list(folder_tree_as_list(folder)))
        queryset = Folder.objects.filter(id__in=[o.id for o in folders])
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        data = serializer.data
        return JsonResponse(data, safe=False)

class OerSerializer(commons.api.OerSerializer):
    class Meta:
        model = OER
        fields = ('id', 'local_path', 'url', 'title', 'project_id', 'modified', 'editor_id', 'n_attachments',)

    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    n_attachments = serializers.SerializerMethodField()
    def get_n_attachments(self, obj):
        return OerDocument.objects.filter(oer_id=obj['id']).count()

class FilteredOerViewSet(commons.api.OerViewSet):
    """ API endpoint for listing OERs. """
    serializer_class = OerSerializer
    http_method_names = ['get', 'head', 'options',]

    def get_queryset(self):
        community = Project.objects.get(slug=root)
        projects = tree_to_list(project_tree_as_list(community))
        queryset = super(FilteredOerViewSet, self).get_queryset()
        return queryset.filter(project__in=projects, state=PUBLISHED).values().order_by('-modified')

    def list(self, request):
        serializer = self.serializer_class(self.get_queryset(), many=True, context={'request': request})
        data = serializer.data
        return JsonResponse(data, safe=False)

class LearningPathSerializer(commons.api.LearningPathSerializer):
    class Meta:
        model = LearningPath
        fields = ('id', 'local_path', 'title', 'short', 'project_id', 'modified', 'editor_id')

    local_path = serializers.ReadOnlyField(source='get_absolute_url')

class FilteredLearningPathViewSet(commons.api.LearningPathViewSet):
    """ API endpoint for listing LPs. """
    serializer_class = LearningPathSerializer
    http_method_names = ['get', 'head', 'options',]

    def get_queryset(self):
        community = Project.objects.get(slug=root)
        projects = tree_to_list(project_tree_as_list(community))
        queryset = super(FilteredLearningPathViewSet, self).get_queryset()
        return queryset.filter(project__in=projects, state=PUBLISHED).values().order_by('-modified')

    def list(self, request):
        serializer = self.serializer_class(self.get_queryset(), many=True, context={'request': request})
        data = serializer.data
        return JsonResponse(data, safe=False)

class FolderDocumentSerializer(commons.api.FolderDocumentSerializer):
    class Meta:
        model = FolderDocument
        fields = ['id', 'local_path', 'label', 'project',]

    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    label = serializers.SerializerMethodField()
    def get_label(self, obj):
        return obj.document and obj.document.label or ''
    project = serializers.SerializerMethodField()
    def get_project(self, obj):
        return obj.folder.get_project().name

class FilteredFolderDocumentViewSet(commons.api.FolderDocumentViewSet):
    """ API endpoint for listing documents in project folders. """
    serializer_class = FolderDocumentSerializer
    http_method_names = ['get', 'head', 'options',]

    def list(self, request):
        community = Project.objects.get(slug=root)
        projects = tree_to_list(project_tree_as_list(community))
        folders = []
        for project in projects:
            folder = project.get_folder()
            folders.extend(tree_to_list(folder_tree_as_list(folder)))
        folder_documents = []
        for folder in folders:
            documents = FolderDocument.objects.filter(folder=folder)
            if documents:
                folder_documents.extend(documents)
        queryset = FolderDocument.objects.filter(id__in=[o.id for o in folder_documents])
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        data = serializer.data
        return JsonResponse(data, safe=False)

CONTENTTYPE_DICT = {}
class ActionSerializer(commons.api.ActionSerializer):
    class Meta:
        model = Action
        # fields = ('actor_object_id', 'verb', 'action_object_content_type_id', 'action_object_object_id', 'target_content_type_id', 'target_object_id', 'description', 'timestamp')
        fields = ('actor_object_id', 'verb', 'object_type', 'action_object_object_id', 'target_type', 'target_object_id', 'description', 'timestamp')

    object_type = serializers.SerializerMethodField()
    def get_object_type(self, obj):
        global CONTENTTYPE_DICT
        return CONTENTTYPE_DICT[obj.action_object_content_type_id]
    target_type = serializers.SerializerMethodField()
    def get_target_type(self, obj):
        target_type_id = obj.target_content_type_id
        global CONTENTTYPE_DICT
        return target_type_id and CONTENTTYPE_DICT[target_type_id] or ''

class FilteredActionViewSet(commons.api.ActionViewSet):
    """ API endpoint for listing actions in stream filtered by project. """
    serializer_class = ActionSerializer
    http_method_names = ['get', 'head', 'options',]
    permission_classes = [IsAuthenticated]

    def get_queryset(self, max_actions=0):
        global CONTENTTYPE_DICT
        CONTENTTYPE_DICT = make_contenttype_dict()
        community = Project.objects.get(slug=root)
        projects = tree_to_list(project_tree_as_list(community))
        project_ids = [project.id for project in projects]
        project_content_type = ContentType.objects.get_for_model(Project)
        queryset = Action.objects.filter(Q(Q(action_object_content_type=project_content_type) & Q(action_object_object_id__in=project_ids)) | Q(Q(target_content_type=project_content_type) & Q(target_object_id__in=project_ids)))
        if max_actions:
            queryset = queryset[:max_actions]
        return queryset

    # @permission_classes([IsAuthenticated])
    def list(self, request, max_actions=1000):
        if not request.user.is_authenticated or not request.user in site_member_users():
            return HttpResponse(403, 'Permission Denied')
        queryset = self.get_queryset(max_actions=max_actions)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        data = serializer.data
        return JsonResponse(data, safe=False)


def register_filtered_endpoints():
    router.register(r'success/users', FilteredUserViewSet)
    router.register(r'success/projects', FilteredProjectViewSet)
    router.register(r'success/folders', FilteredFolderViewSet)
    router.register(r'success/oers', FilteredOerViewSet)
    router.register(r'success/lps', FilteredLearningPathViewSet)
    router.register(r'success/folder_documents', FilteredFolderDocumentViewSet)
    router.register(r'success/actions', FilteredActionViewSet)

register_filtered_endpoints()
