import unittest
import numpy as np
from solver import _dhash, _hamming, _similarity, _looks_like_face


class ImageMatchingTests(unittest.TestCase):
    def test_identical_images_have_zero_hash_distance(self):
        image = np.zeros((100, 80, 3), dtype=np.uint8)
        image[15:85, 20:60] = 180
        self.assertEqual(_hamming(_dhash(image), _dhash(image.copy())), 0)

    def test_identical_images_have_full_similarity(self):
        image = np.random.default_rng(4).integers(0, 255, (100, 80, 3), dtype=np.uint8)
        self.assertGreaterEqual(_similarity(image, image.copy()), 0.999)

    def test_blank_card_is_not_a_face(self):
        image = np.full((100, 80, 3), 245, dtype=np.uint8)
        self.assertFalse(_looks_like_face(image))


if __name__ == "__main__":
    unittest.main()
