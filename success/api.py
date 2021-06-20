from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import routers, serializers, viewsets

import commons
from commons.models import Project, OER, OerDocument, LearningPath, Folder, FolderDocument
from commons.models import PROJECT_OPEN, PUBLISHED
from commons.user_spaces import project_tree_as_list, folder_tree_as_list, tree_to_list, filter_documents
from commons.api import router
# from commons.api import ProjectSerializer, FolderSerializer, FolderDocumentSerializer
# from commons.api import OerSerializer, LearningPathSerializer

root = 'success-erasmus'

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

class ProjectViewSet(commons.api.ProjectViewSet):
    queryset = Project.objects.all().order_by('-created')
    serializer_class = ProjectSerializer
    http_method_names = ['head', 'get', 'post',]

    def list(self, request):
        community = Project.objects.get(slug=root)
        data = project_tree_as_dict(community, request)
        return JsonResponse(data)

router.register(r'success/projects', ProjectViewSet)

class FolderSerializer(commons.api.FolderSerializer):
    class Meta:
        model = Folder
        fields = ('id', 'title', 'project_name',)

    project_name = serializers.SerializerMethodField()
    def get_project_name(self, obj):
        return obj.get_project().name

class FolderViewSet(commons.api.FolderViewSet):
    """ API endpoint for listing project folders. """
    serializer_class = FolderSerializer

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

router.register(r'success/folders', FolderViewSet)

class OerSerializer(commons.api.OerSerializer):
    class Meta:
        model = OER
        fields = ('id', 'local_path', 'url', 'title', 'project_id', 'modified', 'editor_id', 'n_attachments',)

    local_path = serializers.ReadOnlyField(source='get_absolute_url')
    n_attachments = serializers.SerializerMethodField()
    def get_n_attachments(self, obj):
        return OerDocument.objects.filter(oer_id=obj['id']).count()

class OerViewSet(commons.api.OerViewSet):
    """ API endpoint for listing OERs. """
    serializer_class = OerSerializer

    def list(self, request):
        community = Project.objects.get(slug=root)
        projects = tree_to_list(project_tree_as_list(community))
        queryset = OER.objects.filter(project__in=projects, state=PUBLISHED).values().order_by('-modified')
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        data = serializer.data
        return JsonResponse(data, safe=False)

router.register(r'success/oers', OerViewSet)

class LearningPathSerializer(commons.api.LearningPathSerializer):
    class Meta:
        model = LearningPath
        fields = ('id', 'local_path', 'title', 'short', 'project_id', 'modified', 'editor_id')

    local_path = serializers.ReadOnlyField(source='get_absolute_url')

class LearningPathViewSet(commons.api.LearningPathViewSet):
    """ API endpoint for listing LPs. """
    serializer_class = LearningPathSerializer

    def list(self, request):
        community = Project.objects.get(slug=root)
        projects = tree_to_list(project_tree_as_list(community))
        queryset = LearningPath.objects.filter(project__in=projects, state=PUBLISHED).values().order_by('-modified')
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        data = serializer.data
        return JsonResponse(data, safe=False)

router.register(r'success/lps', LearningPathViewSet)


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

class FolderDocumentViewSet(commons.api.FolderDocumentViewSet):
    """ API endpoint for listing documents in project folders. """
    serializer_class = FolderDocumentSerializer

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

router.register(r'success/folder_documents', FolderDocumentViewSet)
