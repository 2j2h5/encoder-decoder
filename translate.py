import torch
import pickle
import random
from attention_model import Encoder, AttnDecoder
from util import *

pkl_file = "multi30k-en-de.pkl"
src_lang = "en"
tgt_lang = "de"

with open(pkl_file, "rb") as f:
    loaded_data = pickle.load(f)

train_pairs = loaded_data["train_pairs"]
valid_pairs = loaded_data["valid_pairs"]
test_pairs = loaded_data["test_pairs"]
src_W2I = loaded_data[f"{src_lang}_W2I"]
src_I2W = loaded_data[f"{src_lang}_I2W"]
tgt_W2I = loaded_data[f"{tgt_lang}_W2I"]
tgt_I2W = loaded_data[f"{tgt_lang}_I2W"]
src_vocab_size = loaded_data[f"{src_lang}_WrdCnt"]
tgt_vocab_size = loaded_data[f"{tgt_lang}_WrdCnt"]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
max_length = 40
hidden_size = 1000
num_layers = 1
dropout_p = 0.1
translate_model = "translate_model(1000-160).pth"

SOS_token = tgt_W2I["<SOS>"]
EOS_token = tgt_W2I["<EOS>"]
UNK_token = tgt_W2I["<UNK>"]
PAD_token = tgt_W2I["<PAD>"]

encoder = Encoder(src_vocab_size, hidden_size, num_layers, device).to(device)
attn_decoder = AttnDecoder(hidden_size, tgt_vocab_size, num_layers, device, dropout_p=dropout_p, max_length=max_length).to(device)

checkpoint = torch.load(translate_model, map_location=device)
encoder.load_state_dict(checkpoint['encoder_state_dict'])
attn_decoder.load_state_dict(checkpoint['attn_decoder_state_dict'])

encoder.eval()
attn_decoder.eval()

def translate(sentence):
    indice = indexesFromSentence(sentence, src_W2I)
    indice.append(EOS_token)

    input_tensor = torch.tensor(indice, dtype=torch.long, device=device).unsqueeze(1)
    input_length = [len(indice)]

    with torch.no_grad():
        encoder_hidden = encoder.initHidden(1)
        encoder_outputs, encoder_hidden = encoder(input_tensor, encoder_hidden)

        encoder_mask = torch.zeros(1, input_tensor.size(0), device=device, dtype=torch.bool)
        encoder_mask[0, :input_length[0]] = True

        decoder_input = torch.tensor([[SOS_token]], device=device)
        decoder_hidden = encoder_hidden

        decoded_words = []
        for t in range(max_length):
            decoder_output, decoder_hidden, attn_weights = attn_decoder(decoder_input, decoder_hidden, encoder_outputs, encoder_mask=encoder_mask)
            topv, topi = decoder_output.topk(1)
            token = topi.item()
            if token == EOS_token:
                break
            decoded_words.append(tgt_I2W.get(token, "<UNK>"))
            decoder_input = topi.transpose(0, 1)

    return " ".join(decoded_words)

if __name__ == "__main__":
    print(f"Number of pair of Sentences: {len(train_pairs)}")
    print(f"Vocab size(en): {src_vocab_size}, Vocab size(de): {tgt_vocab_size}")
    print("Examples of pair of sentences")
    print(f"Number of pair of Sentences: {len(train_pairs)}")
    print(f"Vocab size(en): {src_vocab_size}, Vocab size(de): {tgt_vocab_size}")
    print("Examples of pair of sentences")
    print("-----")
    samples = random.sample(valid_pairs, 10)
    for i in range(10):
        words = samples[i][0].split()
        reversed_words = words[::-1]
        reversed_sentence = ' '.join(reversed_words)
        print(f"Input(en): {reversed_sentence}")
        print(f"Translate(de): {translate(samples[i][0])}")
        print(f"Correct(de): {samples[i][1]}")
        print("-----")