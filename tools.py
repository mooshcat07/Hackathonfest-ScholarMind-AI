
def calculate_average(mark1, mark2, mark3):
    """Calculate the average of three marks."""
    marks = [mark1, mark2, mark3]

    if not all(0 <= mark <= 100 for mark in marks):
        raise ValueError("Marks must be between 0 and 100.")

    return round(sum(marks) / 3, 2)


def calculate_weighted_average(
    mark1, weight1,
    mark2, weight2,
    mark3, weight3
):
    """Calculate a weighted academic average."""

    marks = [mark1, mark2, mark3]
    weights = [weight1, weight2, weight3]

    if not all(0 <= mark <= 100 for mark in marks):
        raise ValueError("Marks must be between 0 and 100.")

    if not all(weight >= 0 for weight in weights):
        raise ValueError("Weights cannot be negative.")

    if sum(weights) != 100:
        raise ValueError("Weights must add up to 100.")

    result = sum(
        mark * weight
        for mark, weight in zip(marks, weights)
    )

    return round(result / 100, 2)


def calculate_percentage(obtained, total):
    """Calculate percentage from obtained and total marks."""

    if total <= 0:
        raise ValueError("Total marks must be greater than zero.")

    if obtained < 0 or obtained > total:
        raise ValueError("Obtained marks must be between zero and total.")

    return round((obtained / total) * 100, 2)


def calculate_required_mark(current_points, final_weight, target):
    """Calculate the mark needed in a final assessment."""

    if not 0 < final_weight <= 100:
        raise ValueError("Final assessment weight must be between 0 and 100.")

    if not 0 <= current_points <= 100:
        raise ValueError("Current weighted points must be between 0 and 100.")

    if not 0 <= target <= 100:
        raise ValueError("Target must be between 0 and 100.")

    required = (target - current_points) / (final_weight / 100)

    return round(required, 2)
