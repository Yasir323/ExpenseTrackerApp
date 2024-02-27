import collections
import heapq


def get_borrowers_and_lenders(expense: list):
    borrowers = collections.defaultdict(int)
    lenders = collections.defaultdict(int)
    for borrower, lender, amount in expense:
        if borrower in lenders:
            lenders[borrower] -= amount
        else:
            borrowers[borrower] += amount
        if lender in borrowers:
            borrowers[lender] -= amount
        else:
            lenders[lender] += amount
    return borrowers, lenders


def simplify_balances(expense: list):
    simplified_expenses = []
    borrowers, lenders = get_borrowers_and_lenders(expense)
    sorted_borrowers = [(-amount, borrower) for borrower, amount in borrowers.items()]
    heapq.heapify(sorted_borrowers)

    for lender, amount_lent in sorted(lenders.items(), key=lambda item: item[1], reverse=True):

        while borrowers and amount_lent > 0:
            amount_borrowed, borrower = heapq.heappop(sorted_borrowers)

            # If borrower and lender are same, skip and get the next borrower
            if borrower == lender:
                amount_borrowed_, borrower_ = amount_borrowed, borrower
                amount_borrowed, borrower = heapq.heappop(sorted_borrowers)
                heapq.heappush(sorted_borrowers, (amount_borrowed_, borrower_))

            amount_borrowed = -amount_borrowed
            amount_transfered = min(amount_borrowed, amount_lent)
            if amount_transfered > 0:
                simplified_expenses.append(f"{borrower} sends {amount_transfered} to {lender}\n")
                updated_amount_borrowed = amount_borrowed - amount_transfered
                updated_amount_lent = amount_lent - amount_transfered
                amount_lent = updated_amount_lent
                if updated_amount_borrowed > 0:
                    heapq.heappush(sorted_borrowers, (-updated_amount_borrowed, borrower))


if __name__ == "__main__":

    # Test Case 1
    expense = [('A', 'B', 250), ('B', 'C', 200)]  # (borrower, lender, amount)
    print("Test Case 1:", expense)
    print(simplify_balances(expense))

    # Test Case 2
    expenses = [('A', 'B', 200), ('B', 'C', 200), ('C', 'A', 100)]
    print("Test Case 2:", expenses)
    print(simplify_balances(expenses))

    # Test Case 3
    expenses = [('A', 'B', 200), ('B', 'C', 200), ('C', 'A', 200)]
    print("Test Case 3:", expenses)
    print(simplify_balances(expenses))

    # Test Case 4
    expenses = [('A', 'B', 200), ('B', 'C', 100), ('A', 'C', 100)]
    print("Test Case 4:", expenses)
    print(simplify_balances(expenses))

    # Test Case 5
    expenses = [('A', 'B', 250), ('B', 'C', 100), ('A', 'C', 120), ('D', 'A', 75)]
    print("Test Case 4:", expenses)
    print(simplify_balances(expenses))
