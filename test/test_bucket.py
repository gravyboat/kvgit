import os
import unittest
import shutil
import kvgit.bucket
import kvgit.errors


class BucketTestCase(unittest.TestCase):
    def setUp(self):
        """
        Create a (local) test repository.
        """
        if os.path.lexists('_test_temp'):
            shutil.rmtree('_test_temp')
        os.mkdir('_test_temp')
        self.test_repo_path = '_test_temp/test.git'
        self.bucket = kvgit.bucket.Bucket(path=self.test_repo_path,
                                          author=('test', 'test@test'))

    def tearDown(self):
        """
        Remove temporary files.
        """
        shutil.rmtree('_test_temp')

    def test_clone(self):
        path = '_test_temp/cloned.git'
        kvgit.bucket.Bucket(path=path, remote=self.test_repo_path)
        self.assertTrue(os.path.isdir(path))
        shutil.rmtree(path)

    def test_init_existing(self):
        kvgit.bucket.Bucket(path=self.test_repo_path)

    def test_remote_mismatch(self):
        with self.assertRaises(kvgit.errors.RemoteMismatch):
            kvgit.bucket.Bucket(path=self.test_repo_path, remote='foo')
        path = '_test_temp/cloned.git'
        kvgit.bucket.Bucket(path=path, remote=self.test_repo_path)
        with self.assertRaises(kvgit.errors.RemoteMismatch):
            kvgit.bucket.Bucket(path=path, remote='foo')

    def test_update_fetch(self):
        b1 = kvgit.bucket.Bucket(path='_test_temp/clone1.git',
                                 remote=self.test_repo_path)
        b2 = kvgit.bucket.Bucket(path='_test_temp/clone2.git',
                                 remote=self.test_repo_path)
        b1.commit('foo', 'bar')
        self.assertEqual(b2.get('foo'), None)
        b2.update()
        self.assertEqual(b2.get('foo'), 'bar')

    def test_update_conflict(self):
        b1 = kvgit.bucket.Bucket(path='_test_temp/clone1.git',
                                 remote=self.test_repo_path)
        b2 = kvgit.bucket.Bucket(path='_test_temp/clone2.git',
                                 remote=self.test_repo_path)
        b1.commit('foo', 'bar')
        with self.assertRaises(kvgit.errors.CommitError):
            b2.commit('foo', 'foo')
        self.assertEqual(b2['foo'], 'bar')

    def test_key_test(self):
        for key in ('/', '//', '/foo', '/foo/bar', 'foo/', 'foo//bar'):
            with self.assertRaises(kvgit.errors.InvalidKey):
                kvgit.bucket._test_key(key)

    def test_set(self):
        self.bucket['foo/bar'] = 'bar'
        self.assertEqual(self.bucket['foo/bar'], 'bar')

    def test_get_absent(self):
        self.assertEqual(self.bucket.get('not/here'), None)
        with self.assertRaises(KeyError):
            self.bucket['not/here']

    def test_commit(self):
        self.bucket['foo/bar'] = 'bar'
        self.bucket.commit()
        self.assertEqual(self.bucket._staged, {})
        self.assertEqual(self.bucket.get('foo/bar'), 'bar')
        self.bucket['biz/baz'] = 'bar'
        self.bucket.commit()
        self.assertEqual(self.bucket.get('biz/baz'), 'bar')
        self.assertEqual(self.bucket.get('foo/bar'), 'bar')

    def test_get_not_staged(self):
        self.bucket['foo'] = 'foo'
        self.bucket.commit()
        self.bucket['foo'] = 'bar'
        self.assertEqual(self.bucket.get('foo', staged=False), 'foo')