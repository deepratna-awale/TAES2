"""
Test data for TAES 2 development and testing
"""

SAMPLE_QUESTION_PAPER = """
Mathematics Final Examination
Total Marks: 100
Time: 3 Hours

Q1. Define the following terms with examples: (10 marks)
a) Function (5 marks)
b) Domain and Range (5 marks)

Q2. Solve the following equations: (20 marks)
a) 2x + 5 = 15 (10 marks)
b) x² - 4x + 4 = 0 (10 marks)

Q3. Explain the concept of limits in calculus with at least two examples. Discuss why limits are important in mathematical analysis. (25 marks)

Q4. Prove that the sum of first n natural numbers is n(n+1)/2. Show all steps clearly. (20 marks)

Q5. Short answer questions: (25 marks)
a) What is the derivative of sin(x)? (5 marks)
b) State the fundamental theorem of calculus. (10 marks)
c) Define continuity of a function. (10 marks)
"""

SAMPLE_ANSWER_SHEET_1 = """
Student Name: John Smith
Mathematics Final Examination

1. a) A function is a mathematical relation where each input has exactly one output. 
   Example: f(x) = 2x + 1 is a function because for every x value, there is exactly one y value.
   
   b) Domain is the set of all possible input values for a function. Range is the set of all possible output values.
   Example: For f(x) = x², domain is all real numbers, range is [0, ∞).

2. a) 2x + 5 = 15
   2x = 15 - 5
   2x = 10
   x = 5
   
   b) x² - 4x + 4 = 0
   This is a perfect square: (x - 2)² = 0
   Therefore x = 2

3. A limit is the value that a function approaches as the input approaches a certain value.
   
   Example 1: lim(x→2) (x² - 4)/(x - 2) = lim(x→2) (x + 2) = 4
   Example 2: lim(x→∞) 1/x = 0
   
   Limits are important because they help us understand function behavior at points where the function might not be defined, and they form the foundation for derivatives and integrals.

4. To prove: 1 + 2 + 3 + ... + n = n(n+1)/2
   
   Proof by mathematical induction:
   Base case: n = 1, LHS = 1, RHS = 1(1+1)/2 = 1 ✓
   
   Inductive step: Assume true for k, prove for k+1
   Assume: 1 + 2 + ... + k = k(k+1)/2
   Need to prove: 1 + 2 + ... + k + (k+1) = (k+1)(k+2)/2
   
   LHS = k(k+1)/2 + (k+1) = (k+1)[k/2 + 1] = (k+1)(k+2)/2 = RHS ✓

5. a) The derivative of sin(x) is cos(x).
   
   b) The fundamental theorem of calculus states that differentiation and integration are inverse operations. More precisely, if f is continuous on [a,b] and F is an antiderivative of f, then ∫[a to b] f(x)dx = F(b) - F(a).
   
   c) A function f is continuous at point a if lim(x→a) f(x) = f(a). This means the function has no breaks, jumps, or holes at that point.
"""

SAMPLE_ANSWER_SHEET_2 = """
Student Name: Jane Doe
Mathematics Final Examination

Q1. a) Function is a relation between sets. Each input gives one output.
    Example: y = x + 1
    
    b) Domain is input values. Range is output values.

Q2. a) 2x + 5 = 15
    2x = 10
    x = 5
    
    b) x² - 4x + 4 = 0
    Using quadratic formula: x = (4 ± √(16-16))/2 = 4/2 = 2

Q3. Limits are values functions approach. Important for calculus.
    Example: limit of x² as x approaches 2 is 4.

Q4. Sum = n(n+1)/2
    For n=3: 1+2+3 = 6, and 3(4)/2 = 6, so it works.

Q5. a) cos(x)
    b) Integration and differentiation are opposite
    c) Function has no breaks
"""

def get_sample_data():
    """Get sample data for testing"""
    return {
        "question_paper": SAMPLE_QUESTION_PAPER,
        "answer_sheets": [
            {"name": "john_smith.txt", "content": SAMPLE_ANSWER_SHEET_1},
            {"name": "jane_doe.txt", "content": SAMPLE_ANSWER_SHEET_2}
        ]
    }
