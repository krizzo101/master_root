"""Binary Search Tree implementation with insert, search, and delete operations."""

from typing import Any, List, Optional


class TreeNode:
    """Represents a single node in the binary search tree.

    Attributes:
        value: The value stored in the node.
        left: Reference to the left child node.
        right: Reference to the right child node.
    """

    def __init__(self, value: Any) -> None:
        """Initialize a new tree node.

        Args:
            value: The value to store in the node.
        """
        self.value = value
        self.left: Optional[TreeNode] = None
        self.right: Optional[TreeNode] = None


class BinarySearchTree:
    """A binary search tree data structure implementation.

    This class provides methods for inserting, searching, and deleting nodes
    while maintaining the binary search tree property: for each node, all values
    in the left subtree are less than the node's value, and all values in the
    right subtree are greater than the node's value.

    Attributes:
        root: The root node of the tree.
    """

    def __init__(self) -> None:
        """Initialize an empty binary search tree."""
        self.root: Optional[TreeNode] = None

    def insert(self, value: Any) -> None:
        """Insert a value into the binary search tree.

        If the value already exists in the tree, it will not be inserted again.

        Args:
            value: The value to insert into the tree.

        Raises:
            TypeError: If the value cannot be compared with existing values in the tree.
        """
        if self.root is None:
            self.root = TreeNode(value)
        else:
            self._insert_recursive(self.root, value)

    def _insert_recursive(self, node: TreeNode, value: Any) -> None:
        """Recursively insert a value into the tree.

        Args:
            node: The current node being examined.
            value: The value to insert.

        Raises:
            TypeError: If the value cannot be compared with existing values.
        """
        try:
            if value < node.value:
                if node.left is None:
                    node.left = TreeNode(value)
                else:
                    self._insert_recursive(node.left, value)
            elif value > node.value:
                if node.right is None:
                    node.right = TreeNode(value)
                else:
                    self._insert_recursive(node.right, value)
        except TypeError as e:
            raise TypeError(
                f"Cannot compare value {value} with existing values in tree: {e}"
            )

    def search(self, value: Any) -> bool:
        """Search for a value in the binary search tree.

        Args:
            value: The value to search for.

        Returns:
            True if the value exists in the tree, False otherwise.

        Raises:
            TypeError: If the value cannot be compared with existing values in the tree.
        """
        try:
            return self._search_recursive(self.root, value)
        except TypeError as e:
            raise TypeError(f"Cannot search for value {value}: {e}")

    def _search_recursive(self, node: Optional[TreeNode], value: Any) -> bool:
        """Recursively search for a value in the tree.

        Args:
            node: The current node being examined.
            value: The value to search for.

        Returns:
            True if the value is found, False otherwise.
        """
        if node is None:
            return False

        if value == node.value:
            return True
        elif value < node.value:
            return self._search_recursive(node.left, value)
        else:
            return self._search_recursive(node.right, value)

    def delete(self, value: Any) -> bool:
        """Delete a value from the binary search tree.

        This method handles three cases:
        1. Node with no children (leaf node): Simply remove the node.
        2. Node with one child: Replace the node with its child.
        3. Node with two children: Find the inorder successor (smallest value in
           the right subtree), replace the node's value with the successor's value,
           and delete the successor.

        Args:
            value: The value to delete from the tree.

        Returns:
            True if the value was found and deleted, False if the value was not found.

        Raises:
            TypeError: If the value cannot be compared with existing values in the tree.
        """
        try:
            self.root, deleted = self._delete_recursive(self.root, value)
            return deleted
        except TypeError as e:
            raise TypeError(f"Cannot delete value {value}: {e}")

    def _delete_recursive(
        self, node: Optional[TreeNode], value: Any
    ) -> tuple[Optional[TreeNode], bool]:
        """Recursively delete a value from the tree.

        Args:
            node: The current node being examined.
            value: The value to delete.

        Returns:
            A tuple containing the potentially modified subtree root and a boolean
            indicating whether the deletion was successful.
        """
        if node is None:
            return None, False

        if value < node.value:
            node.left, deleted = self._delete_recursive(node.left, value)
            return node, deleted
        elif value > node.value:
            node.right, deleted = self._delete_recursive(node.right, value)
            return node, deleted
        else:
            if node.left is None and node.right is None:
                return None, True
            elif node.left is None:
                return node.right, True
            elif node.right is None:
                return node.left, True
            else:
                successor = self._find_min(node.right)
                node.value = successor.value
                node.right, _ = self._delete_recursive(node.right, successor.value)
                return node, True

    def _find_min(self, node: TreeNode) -> TreeNode:
        """Find the node with the minimum value in a subtree.

        Args:
            node: The root of the subtree to search.

        Returns:
            The node with the minimum value.
        """
        current = node
        while current.left is not None:
            current = current.left
        return current

    def inorder_traversal(self) -> List[Any]:
        """Perform an inorder traversal of the tree.

        Returns:
            A list of values in ascending order.
        """
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node: Optional[TreeNode], result: List[Any]) -> None:
        """Recursively perform inorder traversal.

        Args:
            node: The current node being visited.
            result: The list to append values to.
        """
        if node is not None:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)

    def is_empty(self) -> bool:
        """Check if the tree is empty.

        Returns:
            True if the tree has no nodes, False otherwise.
        """
        return self.root is None

    def height(self) -> int:
        """Calculate the height of the tree.

        The height is defined as the number of edges on the longest path from
        the root to a leaf. An empty tree has height -1, and a tree with only
        a root node has height 0.

        Returns:
            The height of the tree.
        """
        return self._height_recursive(self.root)

    def _height_recursive(self, node: Optional[TreeNode]) -> int:
        """Recursively calculate the height of a subtree.

        Args:
            node: The root of the subtree.

        Returns:
            The height of the subtree.
        """
        if node is None:
            return -1
        return 1 + max(
            self._height_recursive(node.left), self._height_recursive(node.right)
        )


if __name__ == "__main__":
    bst = BinarySearchTree()

    values = [50, 30, 70, 20, 40, 60, 80]
    for val in values:
        bst.insert(val)

    print("Inorder traversal:", bst.inorder_traversal())

    print("Search for 40:", bst.search(40))
    print("Search for 25:", bst.search(25))

    print("Delete 20 (no children):", bst.delete(20))
    print("After deleting 20:", bst.inorder_traversal())

    print("Delete 30 (one child):", bst.delete(30))
    print("After deleting 30:", bst.inorder_traversal())

    print("Delete 50 (two children):", bst.delete(50))
    print("After deleting 50:", bst.inorder_traversal())

    print("Tree height:", bst.height())
