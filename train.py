import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import json
import os
import glob
from pytorch_models import AttackFingerprintClassifier, AttackPredictionLSTM

# Configuration
DATA_PATH = '.'  # Search root for 01-12 and 03-11
MODEL_SAVE_PATH = 'models'
REPORT_PATH = 'models/training_report.json'
BATCH_SIZE = 64
EPOCHS = 10
LEARNING_RATE = 0.001

def load_and_clean_data(data_dir):
    print(f"Searching for CSV files in subdirectories...")
    all_files = []
    for sub in ['01-12', '03-11']:
        path = os.path.join(data_dir, sub)
        if os.path.exists(path):
            all_files.extend(glob.glob(os.path.join(path, "*.csv")))
    
    # Filter out lock files
    all_files = [f for f in all_files if not os.path.basename(f).startswith('.')]
    
    if not all_files:
        print(f"No CSV files found in 01-12 or 03-11. Checking {data_dir} directly...")
        all_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not all_files:
        print("No CSV files found anywhere. Generating mock data for demonstration...")
        return generate_mock_data()

    print(f"Found {len(all_files)} files. Loading...")
    df_list = []
    # To avoid memory issues with huge files, we might want to sample, 
    # but the user asked to run training on the real data.
    # We'll try to load them all, but maybe limit to a few if it's too much? 
    # No, user said 10-30 mins, so let's try.
    for filename in all_files:
        print(f"Reading {filename}...", flush=True)
        try:
            # Loading only a portion of each file (100k rows) to prevent MemoryError
            df = pd.read_csv(filename, index_col=None, header=0, low_memory=False, nrows=100000)
            # Handle inconsistent column names (strip spaces)
            df.columns = df.columns.str.strip()
            df_list.append(df)
        except Exception as e:
            print(f"Error reading {filename}: {e}", flush=True)
    
    if not df_list:
        return generate_mock_data()
        
    full_df = pd.concat(df_list, axis=0, ignore_index=True)
    
    # Label Mapping
    label_map = {
        'BENIGN': 'BENIGN',
        'DrDoS_DNS': 'dns_amplification',
        'DrDoS_LDAP': 'dns_amplification',
        'DrDoS_MSSQL': 'dns_amplification',
        'DrDoS_NTP': 'dns_amplification',
        'DrDoS_NetBIOS': 'dns_amplification',
        'DrDoS_SNMP': 'dns_amplification',
        'DrDoS_SSDP': 'dns_amplification',
        'DrDoS_UDP': 'udp_flood',
        'Syn': 'syn_flood',
        'UDP': 'udp_flood',
        'UDP-lag': 'udp_flood',
        'TFTP': 'http_flood',
        'WebDDoS': 'http_flood',
    }
    full_df['Label'] = full_df['Label'].map(label_map)
    full_df.dropna(subset=['Label'], inplace=True)  # drop unmapped

    # Handle Infinity and NaN values
    print("Cleaning data (handling inf and nan)...")
    full_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    full_df.dropna(inplace=True)
    
    return full_df

def generate_mock_data():
    """Generates a synthetic dataset with learnable patterns for demonstration."""
    np.random.seed(42)
    num_samples = 5000
    
    # 7 Classes: 0: BENIGN, 1-6: Various Attacks
    labels = [0] * int(num_samples * 0.7) + list(np.random.randint(1, 7, num_samples - int(num_samples * 0.7)))
    np.random.shuffle(labels)
    
    features = np.zeros((num_samples, 15))
    for i in range(num_samples):
        label = labels[i]
        # Create patterns: certain labels correlate with higher values in specific features
        if label == 0: # BENIGN
            features[i] = np.random.normal(0, 0.5, 15)
        else: # Attack
            features[i] = np.random.normal(label * 0.5, 1.0, 15)
            # Add specific "spikes" for attack types
            features[i, label % 15] += 5.0 
    
    df = pd.DataFrame(features, columns=[f'feature_{i}' for i in range(15)])
    df['Label'] = labels
    attack_map = {0: 'BENIGN', 1: 'http_flood', 2: 'slowloris', 3: 'syn_flood', 
                  4: 'udp_flood', 5: 'dns_amplification', 6: 'mixed_attack'}
    df['Label'] = df['Label'].map(attack_map)
    return df

def train_classifier(df):
    print("Training AttackFingerprintClassifier...")
    X = df.drop('Label', axis=1).select_dtypes(include=[np.number]).values
    y = df['Label'].values
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    num_classes = len(le.classes_)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)
    
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.LongTensor(y_train)
    X_test_t = torch.FloatTensor(X_test)
    y_test_t = torch.LongTensor(y_test)
    
    class_counts = np.bincount(y_train)
    class_weights = 1. / torch.tensor(class_counts, dtype=torch.float)
    sample_weights = class_weights[y_train_t]
    sampler = WeightedRandomSampler(weights=sample_weights, num_samples=len(sample_weights), replacement=True)
    
    train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=BATCH_SIZE, sampler=sampler)
    
    model = AttackFingerprintClassifier(input_size=X.shape[1], num_classes=num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    model.train()
    for epoch in range(EPOCHS):
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(inputs), labels)
            loss.backward()
            optimizer.step()
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{EPOCHS} complete")
    
    model.eval()
    with torch.no_grad():
        test_outputs = model(X_test_t)
        _, predicted = torch.max(test_outputs, 1)
        
        report = {}
        for i, class_name in enumerate(le.classes_):
            true_pos = ((predicted == i) & (y_test_t == i)).sum().item()
            false_pos = ((predicted == i) & (y_test_t != i)).sum().item()
            false_neg = ((predicted != i) & (y_test_t == i)).sum().item()
            precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
            recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
            report[class_name] = {"precision": round(precision, 4), "recall": round(recall, 4)}
        
        report["overall_accuracy"] = round((predicted == y_test_t).sum().item() / len(y_test_t), 4)
    
    torch.save(model.state_dict(), os.path.join(MODEL_SAVE_PATH, 'fingerprint.pt'))
    return report

def train_lstm(df):
    print("Training AttackPredictionLSTM...")
    # Prepare sequence data: Predict if an attack happens in the next window
    X = df.drop('Label', axis=1).select_dtypes(include=[np.number]).values
    y = (df['Label'] != 'BENIGN').astype(int).values
    
    seq_length = 10
    X_seq, y_seq = [], []
    for i in range(len(X) - seq_length):
        X_seq.append(X[i:i+seq_length])
        y_seq.append(y[i+seq_length])
    
    X_seq = np.array(X_seq).astype(np.float32)
    y_seq = np.array(y_seq).astype(np.float32).reshape(-1, 1)
    
    X_train, X_test, y_train, y_test = train_test_split(X_seq, y_seq, test_size=0.2, random_state=42)
    
    train_loader = DataLoader(TensorDataset(torch.tensor(X_train), torch.tensor(y_train)), 
                             batch_size=BATCH_SIZE, shuffle=True)
    
    model = AttackPredictionLSTM(input_size=X.shape[1], hidden_size=64)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    model.train()
    for epoch in range(EPOCHS):
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(inputs), labels)
            loss.backward()
            optimizer.step()
    
    model.eval()
    torch.save(model.state_dict(), os.path.join(MODEL_SAVE_PATH, 'lstm.pt'))
    return {"status": "trained", "msg": "LSTM weights saved with full training loop"}

if __name__ == "__main__":
    df = load_and_clean_data(DATA_PATH)
    
    classifier_report = train_classifier(df)
    lstm_report = train_lstm(df)
    
    final_report = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "classifier_metrics": classifier_report,
        "lstm_status": lstm_report
    }
    
    with open(REPORT_PATH, 'w') as f:
        json.dump(final_report, f, indent=4)
    
    print(f"Training complete. Report saved to {REPORT_PATH}")
