import math

def prob_correct(theta, a, b):
    return 1 / (1 + math.exp(-1.7 * a * (theta - b)))

def update_theta(theta, question, is_correct, lr=0.1):
    a = question.discrimination
    b = question.difficulty
    p = prob_correct(theta, a, b)
    gradient = (is_correct - p)
    return theta + lr * gradient
