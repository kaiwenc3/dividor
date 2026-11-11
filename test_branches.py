import unittest
from chat_graph import branch, build_graph, context_for, message, new_conversation


class BranchTests(unittest.TestCase):
    def test_nested_branches_and_isolation(self):
        root = new_conversation()
        root["messages"] = [message("user", "first"), message("assistant", "answer"),
                            message("user", "later")]
        conversations = {root["id"]: root}
        child = branch(conversations, root["id"], root["messages"][1]["id"], "Child")
        conversations[child]["messages"] = [message("user", "side question")]
        nested = branch(conversations, child, conversations[child]["messages"][0]["id"], "Nested")
        conversations[child]["messages"].append(message("assistant", "later child answer"))
        self.assertEqual([m["content"] for m in context_for(conversations, nested)],
                         ["first", "answer", "side question"])
        self.assertEqual(len(root["messages"]), 3)
        result = build_graph(lambda ctx: str([m["content"] for m in ctx])).invoke(
            {"conversations": conversations, "conversation_id": nested, "prompt": "new"})
        self.assertEqual(result["answer"], "['first', 'answer', 'side question', 'new']")
        self.assertEqual(conversations[nested]["messages"], [])
        with self.assertRaises(ValueError):
            branch(conversations, root["id"], "missing", "Invalid")


if __name__ == "__main__":
    unittest.main()
