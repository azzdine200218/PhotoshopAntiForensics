from PIL import Image
import numpy as np

# Create perfectly distinct donor and doctored images
def create_test_images():
    # Doctored: A bright reddish image with distinct gradient
    doc_array = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(200):
        doc_array[i, :, 0] = min(255, 100 + i)
        doc_array[i, :, 1] = 50
        doc_array[i, :, 2] = 50
    # Add fake PRNU noise signature A
    doc_array = doc_array + np.random.normal(0, 5, doc_array.shape).astype(np.int16)
    doc_img = Image.fromarray(np.clip(doc_array, 0, 255).astype(np.uint8), 'RGB')
    doc_img.save('test_doctored.jpg', quality=90)

    # Donor: A dark bluish image with completely different gradient
    don_array = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(200):
        don_array[:, i, 0] = 20
        don_array[:, i, 1] = 40
        don_array[:, i, 2] = min(255, 50 + i)
    # Add true PRNU noise signature B
    don_array = don_array + np.random.normal(0, 10, don_array.shape).astype(np.int16)
    don_img = Image.fromarray(np.clip(don_array, 0, 255).astype(np.uint8), 'RGB')
    don_img.save('test_donor.jpg', quality=95)

if __name__ == "__main__":
    create_test_images()
    print("Distinct test images created.")
