from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import routers, serializers, viewsets

from commons.models import Project, OER, LearningPath, Folder, FolderDocument
from commons.models import PROJECT_OPEN, PUBLISHED
from commons.user_spaces import project_tree_as_list, folder_tree_as_list, tree_to_list, filter_documents
from commons.api import router
from commons.api import ProjectSerializer, FolderSerializer, FolderDocumentSerializer
from commons.api import OerSerializer, LearningPathSerializer

root = 'success-erasmus'

""" recursively computes the project tree with root in the given project,
    including all project and community types """
def project_tree_as_dict(project, request):
    serializer = ProjectSerializer(project, context={'request': request})
    tree = serializer.data
    children = project.get_children(states=[PROJECT_OPEN], all_proj_type_public=True)
    if children:
        tree['children'] = [project_tree_as_dict(child, request) for child in children]
    return tree

class ProjectViewSet(viewsets.ViewSet):
    queryset = Project.objects.all().order_by('-created')
    serializer_class = ProjectSerializer

    def list(self, request):
        community = Project.objects.get(slug=root)
        data = project_tree_as_dict(community, request)
        return JsonResponse(data)

    def retrieve(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        serializer = ProjectSerializer(project)
        return JsonResponse(serializer.data)

router.register(r'success/projects', ProjectViewSet)

class OerViewSet(viewsets.ModelViewSet):
    """ API endpoint  for listing learning OERs. """
    community = Project.objects.get(slug=root)
    projects = tree_to_list(project_tree_as_list(community))
    queryset = OER.objects.filter(project__in=projects, state=PUBLISHED).order_by('-modified')
    serializer_class = OerSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'state', 'project', 'creator', 'editor')

router.register(r'success/oers', OerViewSet)

class LearningPathViewSet(viewsets.ModelViewSet):
    """ API endpoint  for listing learning paths. """
    community = Project.objects.get(slug=root)
    projects = tree_to_list(project_tree_as_list(community))
    queryset = LearningPath.objects.filter(project__in=projects, state=PUBLISHED).order_by('-modified')
    serializer_class = LearningPathSerializer
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ('id', 'state', 'project', 'creator', 'editor')

router.register(r'success/lps', LearningPathViewSet)

""" recursively computes the folder tree with root in the given project. """
def folder_tree_as_dict(project, request):
    serializer = ProjectSerializer(project, context={'request': request})
    tree = serializer.data
    children = project.get_children(states=[PROJECT_OPEN], all_proj_type_public=True)
    if children:
        tree['children'] = [project_tree_as_dict(child, request) for child in children]
    return tree

class FolderViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing project folders. """
    community = Project.objects.get(slug=root)
    projects = tree_to_list(project_tree_as_list(community))
    folders = []
    for project in projects:
        folder = project.get_folder()
        if folder:
            folders.extend(tree_to_list(folder_tree_as_list(folder)))
    queryset = Folder.objects.filter(id__in=[o.id for o in folders])
    serializer_class = FolderSerializer
    http_method_names = ['get', 'head', 'options']

router.register(r'success/folders', FolderViewSet)

class DocumentViewSet(viewsets.ModelViewSet):
    """ API endpoint for listing project folders. """
    community = Project.objects.get(slug=root)
    projects = tree_to_list(project_tree_as_list(community))
    folders = []
    for project in projects:
        folder = project.get_folder()
        if folder:
            folders.extend(tree_to_list(folder_tree_as_list(folder)))
    folder_documents = []
    for folder in folders:
        # documents = FolderDocument.objects.filter(folder=folder, state=PUBLISHED)
        documents = FolderDocument.objects.filter(folder=folder)
        if documents:
            folder_documents.extend(documents)
    queryset = FolderDocument.objects.filter(id__in=[o.id for o in folder_documents])
    serializer_class = FolderDocumentSerializer
    http_method_names = ['get', 'head', 'options']

router.register(r'success/documents', DocumentViewSet)
