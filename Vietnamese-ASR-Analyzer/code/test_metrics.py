from jiwer import wer, cer

ground_truth = "Ở cái nơi rừng thiêng nước độc này"
prediction = "Um có vungınız hab kh"

print("===== KET QUA DANH GIA =====")

print("Ground Truth:")
print(ground_truth)

print("\nWhisper:")
print(prediction)

print("\nWER:")
print(wer(ground_truth, prediction))

print("\nCER:")
print(cer(ground_truth, prediction))