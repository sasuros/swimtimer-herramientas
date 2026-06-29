import unittest

from core.jet4 import DAOConnection


class _Parameter:
    Value = None


class _Parameters:
    def __init__(self):
        self.values = {}

    def Item(self, name):
        return self.values.setdefault(name, _Parameter())


class _Fields:
    def __init__(self, recordset):
        self.recordset = recordset
        self.Count = len(recordset.rows[0]) if recordset.rows else 0

    def Item(self, index):
        class Field:
            Value = self.recordset.rows[self.recordset.position][index]
        return Field()


class _Recordset:
    def __init__(self, rows):
        self.rows = rows
        self.position = 0
        self.Fields = _Fields(self)
        self.closed = False

    @property
    def EOF(self):
        return self.position >= len(self.rows)

    def MoveNext(self):
        self.position += 1

    def Close(self):
        self.closed = True


class _Query:
    def __init__(self, database, sql):
        self.database = database
        self.sql = sql
        self.Parameters = _Parameters()

    def OpenRecordset(self):
        return _Recordset(self.database.rows)

    def Execute(self, option):
        self.database.executed.append((self.sql, option, self.Parameters.values))

    def Close(self):
        pass


class _Database:
    def __init__(self):
        self.rows = [(1, "Club"), (2, "Otro")]
        self.queries = []
        self.executed = []
        self.closed = False

    def CreateQueryDef(self, _name, sql):
        query = _Query(self, sql)
        self.queries.append(query)
        return query

    def Close(self):
        self.closed = True


class _Workspace:
    def __init__(self):
        self.begun = self.committed = self.rolled_back = 0

    def BeginTrans(self): self.begun += 1
    def CommitTrans(self): self.committed += 1
    def Rollback(self): self.rolled_back += 1


class _Workspaces:
    def __init__(self, workspace): self.workspace = workspace
    def Item(self, _index): return self.workspace


class _Engine:
    def __init__(self, workspace): self.Workspaces = _Workspaces(workspace)


class DAOAdapterTests(unittest.TestCase):
    def setUp(self):
        self.database = _Database()
        self.workspace = _Workspace()
        self.connection = DAOConnection(_Engine(self.workspace), self.database)

    def test_select_fetchone_y_fetchall(self):
        cursor = self.connection.cursor().execute("SELECT * FROM Team WHERE Team_no = ?", 6)
        self.assertEqual(self.database.queries[-1].sql, "SELECT * FROM Team WHERE Team_no = [p0]")
        self.assertEqual(cursor.fetchone(), (1, "Club"))
        self.assertEqual(cursor.fetchall(), [(2, "Otro")])

    def test_insert_parametrizado_y_commit(self):
        self.connection.cursor().execute("INSERT INTO Team VALUES (?, ?)", 6, "Club")
        query = self.database.queries[-1]
        self.assertEqual(query.sql, "INSERT INTO Team VALUES ([p0], [p1])")
        self.assertEqual(query.Parameters.Item("p0").Value, 6)
        self.assertEqual(query.Parameters.Item("p1").Value, "Club")
        self.connection.commit()
        self.assertEqual(self.workspace.committed, 1)

    def test_close_revierte_transaccion_pendiente(self):
        self.connection.close()
        self.assertEqual(self.workspace.rolled_back, 1)
        self.assertTrue(self.database.closed)


if __name__ == "__main__":
    unittest.main()
