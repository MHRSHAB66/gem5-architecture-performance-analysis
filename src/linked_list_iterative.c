
#include <stdio.h>
#include <stdlib.h>

struct Node {
    int label;
    struct Node* next;
};


struct Node* createNode(int label) {
    struct Node* newNode = (struct Node*)malloc(sizeof(struct Node));
    newNode->label = label;
    newNode->next = NULL;
    return newNode;
};


struct Node* reverse(struct Node* head) {
    struct Node* previous = NULL;
    struct Node* current = head;

    while (current != NULL) {
        struct Node* next = current->next;
        current->next = previous;
        previous = current;
        current = next;
    }

    return previous;
}


int main() {

    struct Node* head = NULL;
    struct Node* current = NULL;

    for (int i = 1; i <= 10000; i++) {
        if (head == NULL) {
            head = createNode(i);
            current = head;
        } else {
            current->next = createNode(i);
            current = current->next;
        }
    }

    reverse(head);

    return 0;
}
