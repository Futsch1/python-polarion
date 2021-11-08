import unittest

from polarion.polarion import Polarion
from keys import polarion_user, polarion_password, polarion_url, polarion_project_id


class TestPolarionWorkitem(unittest.TestCase):

    executing_project = None
    pol = None

    @classmethod
    def setUpClass(cls):
        cls.pol = Polarion(
            polarion_url, polarion_user, polarion_password)
        cls.executing_project = cls.pol.getProject(
            polarion_project_id)
        cls.global_workitem = cls.executing_project.createWorkitem('task')

        cls.checking_project = cls.pol.getProject(
            polarion_project_id)

        delete_documents = ['_default/Test name', '_default/Reused']
        try:
            for delete_document in delete_documents:
                checking_document = cls.checking_project.getDocument(delete_document)
                if checking_document is not None:
                    checking_document.delete()
        except Exception:
            pass

    def test_create_and_reuse_document(self):
        # Create a document
        executing_document = self.executing_project.createDocument('_default', 'Test name', 'Test title', ['task'], 'relates_to')
        checking_document = self.checking_project.getDocument('_default/Test name')
        self.assertEqual(executing_document.title, checking_document.title)

        # Add headers to it
        heading = executing_document.addHeading('Test')
        executing_document.addHeading('Test2', heading)

        # Create a workitem an move it into the document
        workitem = self.executing_project.createWorkitem('task')
        workitem.title = 'New document task'
        workitem.save()
        workitem.setDescription('New description')
        workitem.moveToDocument(executing_document, heading)

        # Check that the header is the top level item
        top_level_workitem = executing_document.getTopLevelWorkitem()
        self.assertEqual(top_level_workitem.title, 'Test')

        # Check the workitems inside the document
        workitem_titles = [workitem.title for workitem in executing_document.getWorkitems()]
        self.assertListEqual(workitem_titles, ['Test', 'New document task', 'Test2'])

        # Reuse document
        executing_document = self.executing_project.getDocument('_default/Test name')
        reused_document = executing_document.reuse(self.executing_project.id, '_default', 'Reused', 'derived_from')

        # Now update workitem in original document
        workitem.title = 'Newer document task'
        workitem.save()
        workitem.setDescription('Newer description')

        # Make sure that the reused workitem stayed unchanged
        reused_workitems = reused_document.getWorkitems()
        self.assertEqual('New document task', reused_workitems[1].title)

        # Now update the reused document and check that the workitem's fields were updated
        reused_document.update()
        reused_workitems = reused_document.getWorkitems()
        self.assertEqual('Newer document task', reused_workitems[1].title)
        self.assertEqual('Newer description', reused_workitems[1].getDescription())

    def test_save_document(self):
        # Change the title of a document
        executing_document = self.executing_project.getDocument('_default/Test name')

        executing_document.title = 'Changed title'
        executing_document.save()

        checking_document = self.checking_project.getDocument('_default/Test name')
        self.assertEqual('Changed title', checking_document.title)

    def test_get_spaces(self):
        self.assertListEqual(['_default'], self.checking_project.getDocumentSpaces())
        self.assertEqual(2, len(self.checking_project.getDocumentsInSpace('_default')))

    def test_get_children(self):
        executing_document = self.executing_project.getDocument('_default/Test name')

        children = executing_document.getChildren(executing_document.getTopLevelWorkitem())
        workitem_titles = [workitem.title for workitem in children]
        self.assertIn('Newer document task', workitem_titles)
        self.assertIn('Test2', workitem_titles)
