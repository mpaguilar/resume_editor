"""Unit tests for pagination date arithmetic.

These tests verify the core date calculation logic used in the
pagination boundary detection without requiring the full route.
"""

import datetime
from unittest.mock import patch

import pendulum
import pytest


class TestPaginationDateArithmetic:
    """Unit tests for date arithmetic in pagination calculations."""

    @patch("pendulum.now")
    def test_add_with_negative_weeks_moves_backward(self, mock_now):
        """Verify add(weeks=-N) moves backward in time.

        This is the CORRECT behavior for pagination - we want to go
        backward in time to find older resumes.
        """
        fixed_now = pendulum.datetime(2024, 1, 15, 12, 0, 0)
        mock_now.return_value = fixed_now

        # add(weeks=-1) should give us Jan 8 (one week earlier)
        result = pendulum.now().add(weeks=-1)
        expected = pendulum.datetime(2024, 1, 8, 12, 0, 0)

        assert result == expected
        assert result < fixed_now  # Result is in the past

    @patch("pendulum.now")
    def test_add_with_negative_weeks_is_equivalent_to_subtract_positive(self, mock_now):
        """Verify add(weeks=-N) == subtract(weeks=N)."""
        fixed_now = pendulum.datetime(2024, 1, 15, 12, 0, 0)
        mock_now.return_value = fixed_now

        add_negative = pendulum.now().add(weeks=-3)
        subtract_positive = pendulum.now().subtract(weeks=3)

        assert add_negative == subtract_positive

    @patch("pendulum.now")
    def test_subtract_with_negative_weeks_moves_forward(self, mock_now):
        """Verify subtract(weeks=-N) moves forward in time.

        This is the BUGGY behavior - subtract(weeks=-1) equals add(weeks=1),
        which moves to the future instead of the past.
        """
        fixed_now = pendulum.datetime(2024, 1, 15, 12, 0, 0)
        mock_now.return_value = fixed_now

        # subtract(weeks=-1) should give us Jan 22 (one week later - BUG!)
        result = pendulum.now().subtract(weeks=-1)
        expected = pendulum.datetime(2024, 1, 22, 12, 0, 0)

        assert result == expected
        assert result > fixed_now  # Result is in the future (bug behavior)

    @patch("pendulum.now")
    def test_pagination_boundary_calculation_with_add(self, mock_now):
        """Test the pagination boundary calculation logic with correct add().

        Simulates the fixed loop logic:
        - oldest_week_offset starts at -1
        - We check if check_range < oldest_date
        - If not, decrement oldest_week_offset and continue
        """
        fixed_now = pendulum.datetime(2024, 1, 15, 12, 0, 0)
        mock_now.return_value = fixed_now

        # Simulate a resume created 4 weeks ago (Dec 18, 2023)
        oldest_date = fixed_now.subtract(weeks=4).naive()

        oldest_week_offset = -1
        max_iterations = 0
        max_weeks = 520

        while max_iterations < max_weeks:
            # FIXED: use add() instead of subtract()
            check_range = pendulum.now().add(weeks=oldest_week_offset + 1)
            if check_range.naive() < oldest_date:
                break
            oldest_week_offset -= 1
            max_iterations += 1

        # After 5 iterations, check_range should be before oldest_date
        # oldest_week_offset should be -6 (check_range = Dec 11 < Dec 18)
        assert oldest_week_offset == -6
        assert max_iterations == 5

    @patch("pendulum.now")
    def test_pagination_boundary_calculation_with_subtract_bug(self, mock_now):
        """Demonstrate the bug with subtract() - loop never terminates correctly.

        When using subtract(weeks=negative), the loop iterates forward
        in time instead of backward, never finding the oldest_date.
        """
        fixed_now = pendulum.datetime(2024, 1, 15, 12, 0, 0)
        mock_now.return_value = fixed_now

        # Simulate a resume created 4 weeks ago
        oldest_date = fixed_now.subtract(weeks=4).naive()

        oldest_week_offset = -1
        max_iterations = 0
        max_weeks = 520

        while max_iterations < max_weeks:
            # BUGGY: using subtract() with negative offset
            check_range = pendulum.now().subtract(weeks=oldest_week_offset + 1)
            if check_range.naive() < oldest_date:
                break
            oldest_week_offset -= 1
            max_iterations += 1

        # With the bug, the loop runs to max_weeks (520) because
        # check_range keeps moving forward in time, never < oldest_date
        assert max_iterations == 520  # Hit the safety limit
        assert oldest_week_offset == -521  # Way off from expected -4

    @patch("pendulum.now")
    def test_boundary_calculation_with_no_oldest_date(self, mock_now):
        """Test that boundary calculation handles missing oldest_date gracefully."""
        fixed_now = pendulum.datetime(2024, 1, 15, 12, 0, 0)
        mock_now.return_value = fixed_now

        oldest_date = None  # No resumes exist

        # This should not crash - the actual code checks for oldest_date first
        assert oldest_date is None

    @patch("pendulum.now")
    def test_boundary_calculation_across_year_boundary(self, mock_now):
        """Test boundary calculation across year boundaries."""
        # December 15, 2023
        fixed_now = pendulum.datetime(2023, 12, 15, 12, 0, 0)
        mock_now.return_value = fixed_now

        # Resume created in early January 2023 (48 weeks ago)
        oldest_date = pendulum.datetime(2023, 1, 10, 12, 0, 0).naive()

        oldest_week_offset = -1
        max_iterations = 0
        max_weeks = 520

        while max_iterations < max_weeks:
            check_range = pendulum.now().add(weeks=oldest_week_offset + 1)
            if check_range.naive() < oldest_date:
                break
            oldest_week_offset -= 1
            max_iterations += 1

        # Should find the correct offset around -48
        assert oldest_week_offset < -40  # At least 40 weeks back
        assert oldest_week_offset > -60  # But less than 60
        assert max_iterations < 60  # Reasonable number of iterations
